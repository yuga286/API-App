from __future__ import annotations

import json

import frappe
from frappe.utils import cint

from attendenc_integration.api.v1.request import get_payload
from attendenc_integration.services.checkin_service import create_checkin, get_status as get_event_status
from attendenc_integration.services.settings_service import ensure_enabled
from attendenc_integration.utils.responses import IntegrationError, failure, log_unexpected_error, success
from attendenc_integration.utils.security import require_integration_user


@frappe.whitelist(methods=["POST"])
def create(**kwargs):
	payload = get_payload(kwargs)
	try:
		require_integration_user()
		result = create_checkin(payload)
		code = result.pop("code", "OK")
		status = result.pop("status", "created")
		message = "Punch was already processed" if code == "ALREADY_PROCESSED" else "Employee Checkin created successfully"
		return success(code=code, message=message, data={"status": status, **result})
	except IntegrationError as exc:
		return failure(exc.code, exc.message, exc.data)
	except Exception:
		log_unexpected_error("Attendance Integration checkin create failed", payload)
		return failure("INTERNAL_ERROR", "Unable to create Employee Checkin")


@frappe.whitelist(methods=["POST"])
def batch_create(**kwargs):
	try:
		require_integration_user()
		settings = ensure_enabled()
		if not cint(settings.allow_batch_checkin):
			raise IntegrationError("PERMISSION_DENIED", "Batch checkin is disabled")

		payload = get_payload(kwargs)
		logs = payload.get("logs")
		if isinstance(logs, str):
			logs = json.loads(logs)
		if not isinstance(logs, list):
			raise IntegrationError("INVALID_REQUEST", "logs must be an array")

		maximum_batch_size = cint(settings.maximum_batch_size) or 500
		if len(logs) > maximum_batch_size:
			raise IntegrationError(
				"BATCH_LIMIT_EXCEEDED",
				f"Batch size {len(logs)} exceeds maximum_batch_size {maximum_batch_size}",
			)

		results = []
		created = duplicates = failed = 0
		batch_device_id = payload.get("device_id")
		for index, item in enumerate(logs):
			savepoint = f"attendance_integration_row_{index}"
			frappe.db.savepoint(savepoint)
			row = dict(item or {})
			row.setdefault("device_id", batch_device_id)
			try:
				result = create_checkin(row)
				status = result.pop("status", "created")
				code = result.pop("code", "OK")
				if status == "created":
					created += 1
				else:
					duplicates += 1
				results.append({"event_id": row.get("event_id"), "status": status, "code": code, **result})
				frappe.db.release_savepoint(savepoint)
			except IntegrationError as exc:
				failed += 1
				results.append(
					{
						"event_id": row.get("event_id"),
						"status": "failed",
						"code": exc.code,
						"message": exc.message,
					}
				)
				frappe.db.release_savepoint(savepoint)
			except Exception:
				frappe.db.rollback(save_point=savepoint)
				failed += 1
				log_unexpected_error("Attendance Integration batch row failed", row)
				results.append(
					{
						"event_id": row.get("event_id"),
						"status": "failed",
						"code": "INTERNAL_ERROR",
						"message": "Unable to process row",
					}
				)

		return success(
			data={
				"received": len(logs),
				"created": created,
				"duplicates": duplicates,
				"failed": failed,
				"results": results,
			}
		)
	except IntegrationError as exc:
		return failure(exc.code, exc.message, exc.data)
	except Exception:
		log_unexpected_error("Attendance Integration batch create failed")
		return failure("INTERNAL_ERROR", "Unable to process batch")


@frappe.whitelist(methods=["GET"])
def get_status(**kwargs):
	try:
		require_integration_user()
		ensure_enabled()
		payload = get_payload(kwargs)
		data = get_event_status(str(payload.get("event_id") or "").strip())
		return success(data=data)
	except IntegrationError as exc:
		return failure(exc.code, exc.message, exc.data)
	except Exception:
		log_unexpected_error("Attendance Integration get_status failed")
		return failure("INTERNAL_ERROR", "Unable to fetch synchronization status")
