# Attendenc Integration API

Base method path:

```text
/api/method/attendenc_integration.api.v1
```

Protected endpoints require:

```http
Authorization: token API_KEY:API_SECRET
```

Timestamps are site-local datetimes. Send `YYYY-MM-DD HH:MM:SS`; fractional seconds are accepted by Frappe/HRMS but stored without microseconds by the HRMS Employee Checkin controller.

## Response Format

Success:

```json
{
  "success": true,
  "code": "OK",
  "message": "Employee Checkin created successfully",
  "data": {}
}
```

Failure:

```json
{
  "success": false,
  "code": "EMPLOYEE_NOT_FOUND",
  "message": "No employee exists for Attendance Device ID 101",
  "data": null
}
```

## Error Codes

`OK`, `INVALID_REQUEST`, `AUTHENTICATION_REQUIRED`, `PERMISSION_DENIED`, `INTEGRATION_DISABLED`, `DEVICE_DISABLED`, `DEVICE_NOT_FOUND`, `EMPLOYEE_NOT_FOUND`, `EMPLOYEE_INACTIVE`, `DUPLICATE_ATTENDANCE_DEVICE_ID`, `INVALID_TIMESTAMP`, `INVALID_LOG_TYPE`, `INVALID_LATITUDE`, `INVALID_LONGITUDE`, `ALREADY_PROCESSED`, `BATCH_LIMIT_EXCEEDED`, `CHECKIN_CREATION_FAILED`, `HRMS_NOT_AVAILABLE`, `INTERNAL_ERROR`.

## Health

HTTP Method: `GET`

URL: `/api/method/attendenc_integration.api.v1.health.ping`

Authentication: guest allowed; no secrets or system paths are returned.

Success:

```json
{
  "success": true,
  "code": "OK",
  "message": "Attendance Integration API is available",
  "data": {
    "api_version": "v1",
    "integration_enabled": true,
    "hrms_available": true
  }
}
```

## Get Employee

HTTP Method: `GET`

URL: `/api/method/attendenc_integration.api.v1.employees.get_employee`

Required Parameters: `attendance_device_id`

Validation: employee must exist, be active, and be uniquely identified by `Employee.attendance_device_id`.

Example:

```bash
curl -G "https://erp.example.com/api/method/attendenc_integration.api.v1.employees.get_employee" \
  -H "Authorization: token API_KEY:API_SECRET" \
  --data-urlencode "attendance_device_id=101"
```

## Employee Sync

HTTP Method: `GET`

URL: `/api/method/attendenc_integration.api.v1.employees.sync`

Optional Parameters: `modified_since`, `limit`, `offset`, `company`, `active_only`

Returned employee fields: `employee`, `employee_name`, `attendance_device_id`, `status`, `company`, `default_shift`, `modified`.

Sensitive Employee fields such as salary, bank details, personal identity numbers, and private addresses are never returned.

## Create Checkin

HTTP Method: `POST`

URL: `/api/method/attendenc_integration.api.v1.checkins.create`

Required Parameters: `attendance_device_id`, `timestamp`

Recommended Parameter: `event_id`

Optional Parameters: `device_id`, `log_type`, `skip_auto_attendance`, `latitude`, `longitude`

Validation:

- `attendance_device_id` maps to exactly one active Employee.
- `timestamp` includes date and time and is parsed as a site datetime.
- `log_type`, when supplied, must be `IN` or `OUT`.
- `latitude` is between -90 and 90.
- `longitude` is between -180 and 180.
- Device must be registered and enabled when device enforcement is enabled.

Example:

```bash
curl -X POST \
  https://erp.example.com/api/method/attendenc_integration.api.v1.checkins.create \
  -H "Authorization: token API_KEY:API_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "DEVICE01-000001",
    "attendance_device_id": "101",
    "timestamp": "2026-09-08 09:02:14",
    "device_id": "DEVICE01",
    "log_type": "IN"
  }'
```

Idempotency: if the same `event_id` is sent again after processing, no second Employee Checkin is created and the API returns `ALREADY_PROCESSED`.

Without `event_id`, the fallback duplicate check uses Employee, timestamp, device ID, and log type. A configurable tolerance window can be enabled, but `event_id` is the reliable retry contract.

## Batch Create

HTTP Method: `POST`

URL: `/api/method/attendenc_integration.api.v1.checkins.batch_create`

Required Parameters: `logs`

Optional Batch Parameter: `device_id`; used as the default device for rows that omit `device_id`.

Each item is processed independently. One invalid row does not discard valid rows.

```json
{
  "device_id": "DEVICE01",
  "logs": [
    {
      "event_id": "DEVICE01-000001",
      "attendance_device_id": "101",
      "timestamp": "2026-09-08 09:01:03",
      "log_type": "IN"
    }
  ]
}
```

Oversized batches return `BATCH_LIMIT_EXCEEDED`.

## Status

HTTP Method: `GET`

URL: `/api/method/attendenc_integration.api.v1.checkins.get_status`

Required Parameters: `event_id`

Use this after a desktop HTTP timeout to determine whether the server already processed the event.

## Device Heartbeat

HTTP Method: `POST`

URL: `/api/method/attendenc_integration.api.v1.devices.heartbeat`

Required Parameters: `device_id`

Optional Parameters: `app_version`

When registered device enforcement is disabled, heartbeat auto-creates a logical device record. When enforcement is enabled, the device must already exist and be enabled.

## HRMS Auto Attendance

This app only creates Employee Checkin records. Attendance generation remains controlled by HRMS Shift Type, Shift Assignment, Employee Default Shift, Holiday List, late entry, early exit, and working-hour settings.
