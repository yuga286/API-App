from __future__ import annotations

import frappe

from attendenc_integration.api.v1.request import get_payload
from attendenc_integration.services.device_service import heartbeat as update_heartbeat
from attendenc_integration.services.settings_service import ensure_enabled
from attendenc_integration.services.validation_service import validate_device_id
from attendenc_integration.utils.responses import IntegrationError, failure, log_unexpected_error, success
from attendenc_integration.utils.security import require_integration_user


@frappe.whitelist(methods=["POST"])
def heartbeat(**kwargs):
	try:
		require_integration_user()
		ensure_enabled()
		payload = get_payload(kwargs)
		device_id = validate_device_id(payload.get("device_id"), required=True)
		data = update_heartbeat(device_id, payload.get("app_version"))
		return success(message="Device heartbeat recorded", data=data)
	except IntegrationError as exc:
		return failure(exc.code, exc.message, exc.data)
	except Exception:
		log_unexpected_error("Attendance Integration device heartbeat failed")
		return failure("INTERNAL_ERROR", "Unable to record device heartbeat")
