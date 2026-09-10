from __future__ import annotations

import frappe


def get_payload(kwargs: dict) -> dict:
	if kwargs:
		return dict(kwargs)

	if frappe.request and frappe.request.is_json:
		return frappe.request.get_json(silent=True) or {}

	return {key: value for key, value in frappe.form_dict.items() if key != "cmd"}
