from __future__ import annotations

import frappe
from hrms.hr.doctype.employee_checkin.employee_checkin import add_log_based_on_employee_field

from attendenc_integration.services.device_service import resolve_trusted_checkin_device
from attendenc_integration.services.employee_service import get_employee_by_attendance_device_id
from attendenc_integration.services.idempotency_service import (
	existing_processed_response,
	find_fallback_duplicate,
	mark_duplicate,
	mark_employee_resolved,
	mark_failed,
	mark_processing,
	mark_processed,
	reserve_event,
)
from attendenc_integration.services.settings_service import ensure_enabled
from attendenc_integration.services.validation_service import normalize_checkin_payload
from attendenc_integration.utils.responses import IntegrationError


GEOLOCATION_REQUIRED_MESSAGE = "Latitude and longitude values are required for checking in."


def create_checkin(raw_payload: dict) -> dict:
	ensure_enabled()
	payload = normalize_checkin_payload(raw_payload)

	log = None
	employee_name = None
	try:
		log, duplicate_event = reserve_event(payload)
		if duplicate_event:
			processed = existing_processed_response(log)
			if processed:
				return {"status": "duplicate", "code": "ALREADY_PROCESSED", **processed}
			if log.status in ("Received", "Processing"):
				raise IntegrationError("ALREADY_PROCESSED", "Punch is already being processed")

		mark_processing(log)
		employee = get_employee_by_attendance_device_id(payload["attendance_device_id"])
		employee_name = employee.name
		mark_employee_resolved(log, employee_name)

		device = resolve_trusted_checkin_device(payload.get("device_id"))
		payload["device_id"] = device["device_id"]
		payload["latitude"] = device["latitude"]
		payload["longitude"] = device["longitude"]

		fallback_duplicate = find_fallback_duplicate(payload, employee.name)
		if fallback_duplicate:
			mark_duplicate(log, employee.name, fallback_duplicate)
			return {
				"status": "duplicate",
				"code": "ALREADY_PROCESSED",
				"employee": employee.name,
				"employee_checkin": fallback_duplicate,
			}

		doc = add_log_based_on_employee_field(
			employee_field_value=payload["attendance_device_id"],
			timestamp=payload["timestamp"],
			device_id=payload.get("device_id"),
			log_type=payload.get("log_type"),
			skip_auto_attendance=payload.get("skip_auto_attendance"),
			employee_fieldname="attendance_device_id",
			latitude=payload.get("latitude"),
			longitude=payload.get("longitude"),
		)
		mark_processed(log, employee.name, doc.name)
		return {"status": "created", "code": "OK", "employee": employee.name, "employee_checkin": doc.name}
	except IntegrationError as exc:
		mark_failed(log, exc.code, exc.message, employee=employee_name)
		raise
	except Exception as exc:
		code = "GEOLOCATION_REQUIRED" if GEOLOCATION_REQUIRED_MESSAGE in str(exc) else "CHECKIN_CREATION_FAILED"
		mark_failed(log, code, str(exc), employee=employee_name)
		raise IntegrationError(code, str(exc))


def get_status(event_id: str) -> dict:
	if not event_id:
		raise IntegrationError("INVALID_REQUEST", "event_id is required")

	log = frappe.db.get_value(
		"Attendance Integration Log",
		{"event_id": event_id},
		[
			"event_id",
			"status",
			"device_id",
			"attendance_device_id",
			"employee",
			"employee_checkin",
			"event_timestamp",
			"received_at",
			"processed_at",
			"error_code",
			"error_message",
			"retry_count",
		],
		as_dict=True,
	)
	if not log:
		return {"event_id": event_id, "received": False, "processed": False}

	return {
		**dict(log),
		"received": True,
		"processed": log.status == "Processed",
	}
