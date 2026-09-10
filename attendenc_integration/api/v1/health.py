from __future__ import annotations

import importlib.util

import frappe
from frappe.utils import cint

from attendenc_integration.services.settings_service import get_settings
from attendenc_integration.utils.responses import success


@frappe.whitelist(allow_guest=True, methods=["GET"])
def ping():
	settings = get_settings()
	return success(
		message="Attendance Integration API is available",
		data={
			"api_version": "v1",
			"integration_enabled": bool(cint(settings.enabled)),
			"hrms_available": importlib.util.find_spec("hrms") is not None,
		},
	)
