# AI API Contract

## Endpoint

POST /analyze-document

## Request

Content-Type: multipart/form-data

Field:

file

## Response

```json
{
  "riskScore": 0.15,
  "decision": "LOW_RISK",
  "summary": "Document appears authentic"
}
```

## Allowed Decisions

- LOW_RISK
- MEDIUM_RISK
- HIGH_RISK

## Flow

Flutter
↓
Spring Boot
↓
AiService
↓
POST /analyze-document
↓
ML Service
↓
PostgreSQL
↓
Flutter