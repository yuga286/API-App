from __future__ import annotations

import frappe


def execute() -> None:
	logs = frappe.get_all(
		"Attendance Integration Log",
		filters={
			"employee": ["is", "not set"],
			"attendance_device_id": ["is", "set"],
		},
		fields=["name", "attendance_device_id"],
	)

	for log in logs:
		employees = frappe.get_all(
			"Employee",
			filters={"attendance_device_id": log.attendance_device_id, "status": "Active"},
			pluck="name",
			limit_page_length=2,
		)
		if len(employees) != 1:
			continue

		frappe.db.set_value(
			"Attendance Integration Log",
			log.name,
			"employee",
			employees[0],
			update_modified=False,
		)
