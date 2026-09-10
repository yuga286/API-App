from __future__ import annotations

import frappe

from attendenc_integration.utils.responses import IntegrationError

EMPLOYEE_FIELDS = [
	"name",
	"employee_name",
	"attendance_device_id",
	"status",
	"company",
	"default_shift",
	"modified",
]


def employee_response(row: dict) -> dict:
	return {
		"employee": row.get("name"),
		"employee_name": row.get("employee_name"),
		"attendance_device_id": row.get("attendance_device_id"),
		"status": row.get("status"),
		"company": row.get("company"),
		"default_shift": row.get("default_shift"),
		"modified": str(row.get("modified")) if row.get("modified") else None,
	}


def get_employee_by_attendance_device_id(attendance_device_id: str, active_only: bool = True) -> frappe._dict:
	if not attendance_device_id:
		raise IntegrationError("EMPLOYEE_NOT_FOUND", "attendance_device_id is required")

	employees = frappe.get_all(
		"Employee",
		filters={"attendance_device_id": attendance_device_id},
		fields=EMPLOYEE_FIELDS,
		limit=2,
	)

	if not employees:
		raise IntegrationError(
			"EMPLOYEE_NOT_FOUND",
			f"No employee exists for Attendance Device ID {attendance_device_id}",
		)

	if len(employees) > 1:
		raise IntegrationError(
			"DUPLICATE_ATTENDANCE_DEVICE_ID",
			f"Attendance Device ID {attendance_device_id} is assigned to multiple employees",
		)

	employee = frappe._dict(employees[0])
	if active_only and employee.status != "Active":
		raise IntegrationError(
			"EMPLOYEE_INACTIVE",
			f"Employee {employee.name} for Attendance Device ID {attendance_device_id} is not Active",
		)

	return employee


def sync_employees(
	modified_since: str | None = None,
	limit: int = 100,
	offset: int = 0,
	company: str | None = None,
	active_only: bool = True,
) -> list[dict]:
	filters = {"attendance_device_id": ["is", "set"]}
	if modified_since:
		filters["modified"] = [">", modified_since]
	if company:
		filters["company"] = company
	if active_only:
		filters["status"] = "Active"

	rows = frappe.get_all(
		"Employee",
		filters=filters,
		fields=EMPLOYEE_FIELDS,
		order_by="modified asc, name asc",
		limit_start=max(int(offset or 0), 0),
		limit=min(max(int(limit or 100), 1), 1000),
	)
	return [employee_response(row) for row in rows]
