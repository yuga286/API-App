from __future__ import annotations

from frappe.utils import cint
import frappe

from attendenc_integration.api.v1.request import get_payload
from attendenc_integration.services.employee_service import (
	employee_response,
	get_employee_by_attendance_device_id,
	sync_employees,
)
from attendenc_integration.services.settings_service import ensure_enabled
from attendenc_integration.utils.responses import IntegrationError, failure, log_unexpected_error, success
from attendenc_integration.utils.security import require_integration_user


@frappe.whitelist(methods=["GET"])
def get_employee(**kwargs):
	try:
		require_integration_user()
		ensure_enabled()
		payload = get_payload(kwargs)
		employee = get_employee_by_attendance_device_id(str(payload.get("attendance_device_id") or "").strip())
		return success(data=employee_response(employee))
	except IntegrationError as exc:
		return failure(exc.code, exc.message, exc.data)
	except Exception:
		log_unexpected_error("Attendance Integration get_employee failed")
		return failure("INTERNAL_ERROR", "Unable to fetch employee")


@frappe.whitelist(methods=["GET"])
def sync(**kwargs):
	try:
		require_integration_user()
		settings = ensure_enabled()
		if not cint(settings.allow_employee_sync):
			raise IntegrationError("PERMISSION_DENIED", "Employee sync is disabled")

		payload = get_payload(kwargs)
		employees = sync_employees(
			modified_since=payload.get("modified_since"),
			limit=int(payload.get("limit") or 100),
			offset=int(payload.get("offset") or 0),
			company=payload.get("company"),
			active_only=cint(payload.get("active_only", 1)) == 1,
		)
		return success(data={"employees": employees, "count": len(employees)})
	except IntegrationError as exc:
		return failure(exc.code, exc.message, exc.data)
	except Exception:
		log_unexpected_error("Attendance Integration employee sync failed")
		return failure("INTERNAL_ERROR", "Unable to synchronize employees")
