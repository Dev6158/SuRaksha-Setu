# API Contracts

## Base URL

```text
http://localhost:8080/api/v1
```

---

# Authentication APIs

## Login

### Endpoint

```http
POST /auth/login
```

### Request

```json
{
  "username": "user",
  "password": "password123"
}
```

### Response

```json
{
  "token": "jwt_token"
}
```

---

## Register

### Endpoint

```http
POST /auth/register
```

### Request

```json
{
  "username": "new_user",
  "password": "password123"
}
```

### Response

```json
{
  "message": "User registered successfully"
}
```

---

## OTP Verification

### Endpoint

```http
POST /auth/otp/verify
```

### Request

```json
{
  "username": "user",
  "otp": "123456"
}
```

### Response

```json
{
  "verified": true
}
```

---

# Dashboard APIs

## Account Summary

### Endpoint

```http
GET /account/summary
```

### Authentication

Bearer JWT Required

### Response

```json
{
  "totalAccounts": 120,
  "highRiskAccounts": 12,
  "mediumRiskAccounts": 30,
  "lowRiskAccounts": 78
}
```

---

## Risk Event Trends

### Endpoint

```http
GET /analytics/risk-events/trends/hourly
```

### Query Parameters

```text
windowStart
windowEnd
```

### Response

```json
[
  {
    "hour": "08:00",
    "incidents": 5
  }
]
```

---

## High Risk Events

### Endpoint

```http
GET /analytics/risk-events/high-risk
```

### Query Parameters

```text
windowStart
windowEnd
minimumRiskScore
```

---

# Document Upload APIs

## Upload Document

### Endpoint

```http
POST /documents/upload
```

### Request

multipart/form-data

```text
file
```

### Response

```json
{
  "documentId": "123",
  "status": "uploaded"
}
```

---

## Document Types

### Endpoint

```http
GET /documents/types
```

### Response

```json
[
  "AADHAR",
  "PAN",
  "BANK_STATEMENT"
]
```

---

# AI / ML APIs

See `AI_API_CONTRACT.md` for detailed AI service specifications.
