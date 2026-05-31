# Frontend → Backend Integration Guide
## Amrita read ekbar
## Set the Base URL

Open `continuous_auth_service.dart` and `offline_telemetry_cache.dart`.

Both files import `api_service.dart`, which contains the `kBaseUrl` constant.

Replace:

```text
http://10.0.2.2:8080
```

with the deployed backend URL.

All API calls and WebSocket connections across the Flutter application automatically use this value, so this is the only URL change required.

---

## Authentication Endpoints

The application opens on `login_view.dart`.

### Login

```http
POST /api/v1/auth/login
```

Expected response fields:

```text
user_id
session_id
access_token
refresh_token
display_name
masked_account_number
avatar_initials
```

### Registration

```http
POST /api/v1/auth/register
```

Expected response fields are identical to the login response.

### Important

All field names must use:

```text
snake_case
```

Do not return:

```text
camelCase
```

The frontend parser expects exact field names.

After successful authentication, Flutter stores the JWT and automatically sends:

```http
Authorization: Bearer <token>
```

with all future requests.

---

## Dashboard Data

After login, `home_portal_view.dart` immediately performs three parallel requests:

```http
GET /api/v1/account/summary
GET /api/v1/transactions?limit=10&offset=0
GET /api/v1/account/monthly-stats
```

### Account Summary

Used to populate:

* User name
* Account balance
* Account number
* Avatar

### Transactions

Response must contain a `transactions` array.

Each transaction should include:

```text
id
title
subtitle
amount
type
status
date
category
```

Supported `type` values:

```text
credit
debit
```

Supported `status` values:

```text
success
pending
failed
```

Supported `category` values:

```text
transfer
payment
recharge
shopping
food
travel
deposit
```

### Monthly Statistics

Expected fields:

```text
total_income
total_expenses
income_change_percent
expense_change_percent
```

---

## Document Upload

When `upload_wizard_view.dart` loads, it requests:

```http
GET /api/v1/documents/types
```

The response should return a `types` array.

Each type should contain:

```text
id
label
subtitle
is_required
accepted_formats
max_size_mb
```

### Upload Endpoint

```http
POST /api/v1/documents/upload
```

Multipart form fields:

```text
file
document_type_id
```

Expected response fields:

```text
document_id
document_type_id
file_name
status
uploaded_at
```

---

## OTP Verification

`adaptive_security_view.dart` displays the OTP screen when the risk score exceeds 31.

Verification endpoint:

```http
POST /api/v1/auth/otp/verify
```

Request body:

```json
{
  "otp": "123456",
  "session_id": "..."
}
```

Success response:

```json
{
  "verified": true
}
```

Failure response:

```json
{
  "verified": false
}
```

The frontend handles all UI state changes automatically.

---

## WebSocket Telemetry

After login, `continuous_auth_service.dart` opens a persistent WebSocket connection:

```text
ws://<base-url>/api/v1/telemetry/stream
```

Headers included:

```text
X-Session-Id
X-User-Id
Authorization: Bearer <token>
```

### Telemetry Stream

The Flutter application sends telemetry packets every:

```text
100 milliseconds
```

Telemetry contains:

* Accelerometer data
* Gyroscope data
* Swipe metrics
* Tap metrics
* Keystroke intervals

### ML Risk Response

Backend must respond using:

```json
{
  "risk_score": 45,
  "state": "CHALLENGE_OTP"
}
```

Supported states:

```text
TRUSTED
CHALLENGE_OTP
CHALLENGE_BIOMETRIC
FROZEN
```

These values directly control the UI state inside `adaptive_security_view.dart`.

---

## Offline Batch Sync

If connectivity is lost, `offline_telemetry_cache.dart` stores packets locally using Hive.

The frontend automatically retries synchronization every:

```text
10 seconds
```

Batch upload endpoint:

```http
POST /api/v1/telemetry/batch
```

Request body:

```json
{
  "packets": [...]
}
```

Each packet follows the same structure as the real-time WebSocket telemetry packets.

If the backend uses a different endpoint path, please notify the frontend team.

---

## Final Notes

### Monetary Values

```text
float (INR)
```

### Timestamps

```text
Unix Epoch Milliseconds
```

### Transaction Dates

```text
ISO 8601 Strings
```

### JSON Naming Convention

Use:

```text
snake_case
```

Do not use:

```text
camelCase
```

The Flutter models deserialize using exact field names and are case-sensitive.
