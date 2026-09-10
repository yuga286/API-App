from __future__ import annotations

import frappe
from frappe.utils import cint

from attendenc_integration.utils.responses import IntegrationError


DEFAULTS = {
	"enabled": 1,
	"allow_employee_sync": 1,
	"allow_batch_checkin": 1,
	"maximum_batch_size": 500,
	"duplicate_time_tolerance_seconds": 0,
	"enforce_registered_devices": 0,
	"log_integration_requests": 1,
	"log_retention_days": 90,
}


def get_settings() -> frappe._dict:
	if frappe.db.exists("DocType", "Attendance Integration Settings"):
		doc = frappe.get_single("Attendance Integration Settings")
		values = frappe._dict({key: getattr(doc, key, DEFAULTS[key]) for key in DEFAULTS})
		values.default_company = getattr(doc, "default_company", None)
		return values

	return frappe._dict(DEFAULTS | {"default_company": None})


def ensure_enabled() -> frappe._dict:
	settings = get_settings()
	if not cint(settings.enabled):
		raise IntegrationError("INTEGRATION_DISABLED", "Attendance Integration is disabled")
	return settings
