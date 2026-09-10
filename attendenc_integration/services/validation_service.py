from __future__ import annotations

import re

from frappe.utils import cint, flt

from attendenc_integration.utils.datetime import parse_site_datetime
from attendenc_integration.utils.responses import IntegrationError

DEVICE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:/@ -]{1,140}$")


def clean_required_text(value, fieldname: str, code: str = "INVALID_REQUEST") -> str:
	if value is None or str(value).strip() == "":
		raise IntegrationError(code, f"{fieldname} is required")
	return str(value).strip()


def normalize_log_type(value) -> str | None:
	if value is None or str(value).strip() == "":
		return None

	log_type = str(value).strip().upper()
	if log_type not in {"IN", "OUT"}:
		raise IntegrationError("INVALID_LOG_TYPE", "log_type must be IN or OUT when supplied")
	return log_type


def normalize_bool(value, fieldname: str) -> int:
	if value in (None, ""):
		return 0
	if isinstance(value, bool):
		return cint(value)
	if str(value).strip() in {"0", "1"}:
		return cint(value)
	raise IntegrationError("INVALID_REQUEST", f"{fieldname} must be 0 or 1")


def validate_device_id(value, required: bool = False) -> str | None:
	if value is None or str(value).strip() == "":
		if required:
			raise IntegrationError("INVALID_REQUEST", "device_id is required")
		return None

	device_id = str(value).strip()
	if not DEVICE_ID_PATTERN.match(device_id):
		raise IntegrationError("INVALID_REQUEST", "device_id contains unsupported characters or is too long")
	return device_id


def validate_latitude(value) -> float | None:
	if value in (None, ""):
		return None
	latitude = flt(value)
	if latitude < -90 or latitude > 90:
		raise IntegrationError("INVALID_LATITUDE", "latitude must be between -90 and 90")
	return latitude


def validate_longitude(value) -> float | None:
	if value in (None, ""):
		return None
	longitude = flt(value)
	if longitude < -180 or longitude > 180:
		raise IntegrationError("INVALID_LONGITUDE", "longitude must be between -180 and 180")
	return longitude


def normalize_checkin_payload(payload: dict) -> dict:
	attendance_device_id = clean_required_text(
		payload.get("attendance_device_id"), "attendance_device_id", "EMPLOYEE_NOT_FOUND"
	)
	return {
		"event_id": str(payload.get("event_id")).strip() if payload.get("event_id") else None,
		"attendance_device_id": attendance_device_id,
		"timestamp": parse_site_datetime(payload.get("timestamp")),
		"device_id": validate_device_id(payload.get("device_id")),
		"log_type": normalize_log_type(payload.get("log_type")),
		"skip_auto_attendance": normalize_bool(payload.get("skip_auto_attendance"), "skip_auto_attendance"),
		"latitude": validate_latitude(payload.get("latitude")),
		"longitude": validate_longitude(payload.get("longitude")),
	}
