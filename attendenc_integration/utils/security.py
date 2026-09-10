from __future__ import annotations

import frappe

from attendenc_integration.utils.responses import IntegrationError


ALLOWED_ROLES = {"Attendance Integration User", "System Manager", "HR Manager"}


def require_integration_user() -> None:
	if frappe.session.user == "Guest":
		raise IntegrationError("AUTHENTICATION_REQUIRED", "Authentication is required")

	roles = set(frappe.get_roles(frappe.session.user))
	if not roles.intersection(ALLOWED_ROLES):
		raise IntegrationError("PERMISSION_DENIED", "User is not permitted to use Attendance Integration APIs")
