from __future__ import annotations

import frappe
from frappe.utils import now_datetime

from attendenc_integration.services.settings_service import get_settings
from attendenc_integration.utils.responses import IntegrationError


def validate_device(device_id: str | None) -> dict | None:
	settings = get_settings()
	if not settings.enforce_registered_devices:
		return None

	if not device_id:
		raise IntegrationError("DEVICE_NOT_FOUND", "device_id is required when device enforcement is enabled")

	device = frappe.db.get_value(
		"Attendance Integration Device",
		{"device_id": device_id},
		["name", "device_id", "enabled", "company", "latitude", "longitude"],
		as_dict=True,
	)
	if not device:
		raise IntegrationError("DEVICE_NOT_FOUND", f"Device {device_id} is not registered")
	if not device.enabled:
		raise IntegrationError("DEVICE_DISABLED", f"Device {device_id} is disabled")
	return dict(device)


def heartbeat(device_id: str, app_version: str | None = None) -> dict:
	device = frappe.db.get_value(
		"Attendance Integration Device",
		{"device_id": device_id},
		["name", "device_id", "enabled", "company"],
		as_dict=True,
	)
	if not device:
		settings = get_settings()
		if settings.enforce_registered_devices:
			raise IntegrationError("DEVICE_NOT_FOUND", f"Device {device_id} is not registered")

		doc = frappe.get_doc(
			{
				"doctype": "Attendance Integration Device",
				"device_id": device_id,
				"device_name": device_id,
				"enabled": 1,
				"last_seen": now_datetime(),
				"app_version": app_version,
			}
		)
		doc.insert(ignore_permissions=True)
		device = {"name": doc.name, "device_id": doc.device_id, "enabled": doc.enabled, "company": doc.company}
	else:
		frappe.db.set_value(
			"Attendance Integration Device",
			device.name,
			{"last_seen": now_datetime(), "app_version": app_version},
			update_modified=False,
		)

	return {
		"device_id": device.device_id,
		"enabled": bool(device.enabled),
		"permitted": bool(device.enabled),
		"company": device.company,
	}
