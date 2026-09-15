from __future__ import annotations

from datetime import timedelta

import frappe
from frappe.utils import add_days, cint, get_datetime, now_datetime, nowdate

from attendenc_integration.services.settings_service import get_settings


def reserve_event(payload: dict):
	event_id = payload.get("event_id")
	if not event_id:
		return None, False

	existing = frappe.db.get_value(
		"Attendance Integration Log",
		{"event_id": event_id},
		["name", "status", "employee_checkin", "employee", "error_code", "error_message", "retry_count"],
		as_dict=True,
	)
	if existing:
		frappe.db.set_value(
			"Attendance Integration Log",
			existing.name,
			"retry_count",
			cint(existing.retry_count) + 1,
			update_modified=False,
		)
		return frappe.get_doc("Attendance Integration Log", existing.name), True

	try:
		log = frappe.get_doc(
			{
				"doctype": "Attendance Integration Log",
				"event_id": event_id,
				"device_id": payload.get("device_id"),
				"attendance_device_id": payload.get("attendance_device_id"),
				"event_timestamp": payload.get("timestamp"),
				"received_at": now_datetime(),
				"status": "Received",
			}
		)
		log.insert(ignore_permissions=True)
		return log, False
	except frappe.DuplicateEntryError:
		existing_name = frappe.db.get_value("Attendance Integration Log", {"event_id": event_id})
		return frappe.get_doc("Attendance Integration Log", existing_name), True


def existing_processed_response(log) -> dict | None:
	if not log:
		return None
	if log.status in ("Processed", "Duplicate") and log.employee_checkin:
		return {
			"employee": log.employee,
			"employee_checkin": log.employee_checkin,
		}
	return None


def mark_processing(log, employee: str | None = None) -> None:
	if not log:
		return
	log.status = "Processing"
	if employee:
		log.employee = employee
	log.save(ignore_permissions=True)


def mark_employee_resolved(log, employee: str) -> None:
	if not log:
		return
	log.employee = employee
	log.save(ignore_permissions=True)


def mark_processed(log, employee, employee_checkin: str) -> None:
	if not log:
		return
	log.employee = employee
	log.employee_checkin = employee_checkin
	log.status = "Processed"
	log.error_code = None
	log.error_message = None
	log.processed_at = now_datetime()
	log.save(ignore_permissions=True)


def mark_duplicate(log, employee, employee_checkin: str) -> None:
	if not log:
		return
	log.employee = employee
	log.employee_checkin = employee_checkin
	log.status = "Duplicate"
	log.error_code = None
	log.error_message = None
	log.processed_at = now_datetime()
	log.save(ignore_permissions=True)


def mark_failed(log, code: str, message: str, employee: str | None = None) -> None:
	if not log:
		return
	log.status = "Failed"
	if employee:
		log.employee = employee
	log.error_code = code
	log.error_message = message[:1000] if message else None
	log.processed_at = now_datetime()
	log.save(ignore_permissions=True)


def find_fallback_duplicate(payload: dict, employee: str) -> str | None:
	settings = get_settings()
	tolerance = max(cint(settings.duplicate_time_tolerance_seconds), 0)
	timestamp = get_datetime(payload["timestamp"])

	filters = {
		"employee": employee,
		"device_id": payload.get("device_id"),
		"log_type": payload.get("log_type"),
	}
	if tolerance:
		filters["time"] = ["between", [timestamp - timedelta(seconds=tolerance), timestamp + timedelta(seconds=tolerance)]]
	else:
		filters["time"] = timestamp

	return frappe.db.get_value("Employee Checkin", filters, "name")


def cleanup_old_logs() -> None:
	settings = get_settings()
	retention_days = cint(settings.log_retention_days)
	if retention_days <= 0:
		return

	cutoff = add_days(nowdate(), -retention_days)
	for name in frappe.get_all(
		"Attendance Integration Log",
		filters={"status": ["in", ["Processed", "Duplicate", "Failed"]], "modified": ["<", cutoff]},
		pluck="name",
	):
		frappe.delete_doc("Attendance Integration Log", name, ignore_permissions=True)
