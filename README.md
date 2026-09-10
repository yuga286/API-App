# Attendenc Integration

`attendenc_integration` is a custom Frappe app that exposes a secure API layer for desktop biometric attendance software. The app name is intentionally spelled `attendenc_integration`.

The integration flow is:

```text
Desktop App -> attendenc_integration APIs -> Employee -> Employee Checkin -> HRMS Auto Attendance -> Attendance
```

This app does not create Attendance records directly and does not replace HRMS shift or auto attendance logic.

## Investigation Findings

- Installed apps reviewed with `bench version`: Frappe 16.32.0, ERPNext 16.33.0, HRMS 17.0.0-dev.
- HRMS Employee has the standard `attendance_device_id` field added by HRMS setup.
- HRMS Employee Checkin includes `employee`, `employee_name`, `time`, `log_type`, `device_id`, `skip_auto_attendance`, `latitude`, `longitude`, `shift`, `offshift`, and `attendance`.
- HRMS exposes `hrms.hr.doctype.employee_checkin.employee_checkin.add_log_based_on_employee_field`.
- The installed HRMS function accepts `employee_fieldname="attendance_device_id"` plus `device_id`, `log_type`, `skip_auto_attendance`, `latitude`, and `longitude`.
- Shift detection is performed by the Employee Checkin controller through HRMS Shift Assignment and Employee Default Shift logic.

## Installation

```bash
bench --site <site> install-app attendenc_integration
bench --site <site> migrate
```

Create a Frappe user for the desktop integration and assign `Attendance Integration User`. Generate API key/secret for that user and authenticate with:

```http
Authorization: token API_KEY:API_SECRET
```

## Configuration

Open `Attendance Integration Settings`.

- `enabled`: master switch for protected APIs.
- `allow_employee_sync`: enables employee sync endpoint.
- `allow_batch_checkin`: enables batch punch endpoint.
- `maximum_batch_size`: default 500.
- `duplicate_time_tolerance_seconds`: fallback duplicate window when `event_id` is missing.
- `enforce_registered_devices`: requires enabled `Attendance Integration Device` records.
- `log_retention_days`: deletes old custom integration logs only; never Employee Checkin or Attendance.

## API Documentation

See [docs/API.md](docs/API.md).

## Desktop Startup Contract

The desktop app needs:

- ERP URL
- API Key
- API Secret
- Device ID

Startup procedure:

1. Call health API.
2. Authenticate using token auth.
3. Send device heartbeat.
4. Optionally synchronize employees.
5. Start collecting biometric events.

Punch procedure:

1. Read device punch.
2. Assign a globally unique `event_id`.
3. Save the event to the desktop local queue.
4. POST the event to Frappe.
5. Mark it synchronized only after a successful acknowledgement.

Failure procedure:

1. Keep the event queued.
2. Retry later using the same `event_id`.
3. Treat `ALREADY_PROCESSED` as a successful synchronization.

## Tests

```bash
bench --site <site> run-tests --app attendenc_integration
```
