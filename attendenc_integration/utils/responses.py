from __future__ import annotations

import frappe


class IntegrationError(Exception):
	def __init__(self, code: str, message: str, data: dict | None = None):
		super().__init__(message)
		self.code = code
		self.message = message
		self.data = data


def success(code: str = "OK", message: str = "OK", data: dict | list | None = None) -> dict:
	return {
		"success": True,
		"code": code,
		"message": message,
		"data": data or {},
	}


def failure(code: str, message: str, data: dict | list | None = None) -> dict:
	return {
		"success": False,
		"code": code,
		"message": message,
		"data": data,
	}


def log_unexpected_error(title: str, context: dict | None = None) -> None:
	safe_context = dict(context or {})
	for key in list(safe_context):
		if key.lower() in {"authorization", "api_secret", "password", "pwd", "sid", "cookie"}:
			safe_context[key] = "***"

	frappe.log_error(title=title, message=frappe.get_traceback() + "\n\nContext:\n" + frappe.as_json(safe_context))
