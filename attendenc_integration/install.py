import frappe
from frappe.permissions import setup_custom_perms


ROLE = "Attendance Integration User"


def after_install():
	if not frappe.db.exists("Role", ROLE):
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": ROLE,
				"desk_access": 1,
			}
		).insert(ignore_permissions=True)

	if frappe.db.exists("DocType", "Attendance Integration Settings"):
		settings = frappe.get_single("Attendance Integration Settings")
		if settings.maximum_batch_size is None:
			settings.maximum_batch_size = 500
		if settings.duplicate_time_tolerance_seconds is None:
			settings.duplicate_time_tolerance_seconds = 0
		if settings.log_retention_days is None:
			settings.log_retention_days = 90
		settings.save(ignore_permissions=True)

	add_integration_permissions()


def add_integration_permissions():
	ensure_custom_permission("Employee", read=1, select=1)
	ensure_custom_permission("Employee Checkin", read=1, create=1, select=1)


def ensure_custom_permission(doctype: str, **permissions):
	if not frappe.db.exists("DocType", doctype):
		return

	setup_custom_perms(doctype)
	name = frappe.db.get_value(
		"Custom DocPerm",
		{"parent": doctype, "role": ROLE, "permlevel": 0, "if_owner": 0},
	)
	if name:
		doc = frappe.get_doc("Custom DocPerm", name)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "Custom DocPerm",
				"parent": doctype,
				"parenttype": "DocType",
				"parentfield": "permissions",
				"role": ROLE,
				"permlevel": 0,
				"if_owner": 0,
			}
		)

	for fieldname, value in permissions.items():
		setattr(doc, fieldname, value)
	doc.save(ignore_permissions=True)
