from __future__ import annotations

from datetime import datetime

from frappe.utils import get_datetime

from attendenc_integration.utils.responses import IntegrationError


def parse_site_datetime(value) -> datetime:
	if not value:
		raise IntegrationError("INVALID_TIMESTAMP", "timestamp is required")

	if isinstance(value, str):
		raw = value.strip()
		if not raw or (" " not in raw and "T" not in raw):
			raise IntegrationError("INVALID_TIMESTAMP", "timestamp must include date and time")
	else:
		raw = value

	try:
		return get_datetime(raw).replace(microsecond=0)
	except Exception:
		raise IntegrationError("INVALID_TIMESTAMP", "timestamp must be parseable as a site datetime")
