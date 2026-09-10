app_name = "attendenc_integration"
app_title = "Attendenc Integration"
app_publisher = "Vivira"
app_description = "Secure desktop biometric attendance API layer for Frappe, ERPNext and HRMS."
app_email = "admin@example.com"
app_license = "MIT"

required_apps = ["erpnext", "hrms"]

fixtures = [
	{"dt": "Role", "filters": [["name", "in", ["Attendance Integration User"]]]},
]

after_install = "attendenc_integration.install.after_install"
after_migrate = ["attendenc_integration.install.after_install"]

scheduler_events = {
	"daily": [
		"attendenc_integration.services.idempotency_service.cleanup_old_logs",
	]
}
