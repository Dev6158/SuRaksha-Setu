# SuRaksha Setu - DevOps & Infrastructure Guide

## Overview

SuRaksha Setu is a multi-service banking fraud detection and security platform developed collaboratively across Backend, Frontend, AI/ML, and DevOps teams.

The `devops-amrita` branch provides the infrastructure and deployment foundation required to integrate, configure, and run all project services in a unified environment.

Current DevOps deliverables include:

* Docker Compose orchestration
* PostgreSQL deployment
* Redis deployment
* Environment variable management
* Secrets setup automation
* Health check configuration
* CI/CD workflow setup
* OpenAPI placeholder documentation
* Integration testing scaffolding

---

# Repository Structure

```text
SuRaksha-Setu/
│
├── .github/
│   └── workflows/
│       └── deploy.yml
│
├── admin-dashboard/
│
├── infra/
│   ├── docker-compose.yml
│   ├── .env.example
│   └── setup_secrets.sh
│
├── integration-tests/
│   └── test_system_integration.py
│
├── openapi_spec.yaml
├── requirements.txt
├── pom.xml
└── README.md
```

---

# Infrastructure Components

## PostgreSQL

Container:

```text
suraksha-postgres
```

Purpose:

* User information
* Fraud logs
* Analytics records
* Application data

Port:

```text
5432
```

Health Check:

```text
pg_isready
```

---

## Redis

Container:

```text
suraksha-redis
```

Purpose:

* Session management
* Caching
* Temporary storage
* Rate limiting support

Port:

```text
6379
```

Health Check:

```text
redis-cli ping
```

---

## Backend Service

Framework:

```text
Spring Boot
```

Responsibilities:

* Authentication
* JWT management
* Database operations
* WebSocket communication
* API orchestration

Default Port:

```text
8080
```

---

## AI/ML Services

Framework:

```text
FastAPI
```

Current Services Identified:

### Behavioral Analytics

Endpoints:

```text
GET  /health
POST /score
POST /train
GET  /user/{user_id}/status
```

### Forensic Analysis

Endpoints:

```text
GET  /healthz
POST /api/v1/forensics/analyze
```

---

## Dashboard

Purpose:

* Administrative monitoring
* Risk visualization
* Fraud analysis dashboards

Default Port:

```text
3000
```

---

# Environment Configuration

## Setup

Copy:

```bash
cp infra/.env.example infra/.env
```

Update values before running the project.

---

## Important Variables

### Database

```env
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
DB_HOST
DB_PORT
```

### Redis

```env
REDIS_HOST
REDIS_PORT
```

### Security

```env
JWT_SECRET
```

Never commit production secrets to GitHub.

---

# Local Development Setup

## Start Infrastructure

```bash
cd infra

docker compose up -d postgres redis
```

Verify:

```bash
docker ps
```

Expected containers:

```text
suraksha-postgres
suraksha-redis
```

---

## Run Backend

```bash
mvn spring-boot:run
```

Backend URL:

```text
http://localhost:8080
```

---

## Run AI/ML Service

```bash
pip install -r requirements.txt

uvicorn behavioral_analytics_engine:app --host 0.0.0.0 --port 8000
```

---

# Health Checks

## PostgreSQL

```bash
docker exec -it suraksha-postgres pg_isready
```

## Redis

```bash
docker exec -it suraksha-redis redis-cli ping
```

## Behavioral Analytics

```text
GET /health
```

## Forensics Service

```text
GET /healthz
```

---

# CI/CD

GitHub Actions workflow:

```text
.github/workflows/deploy.yml
```

Pipeline validates:

* Spring Boot build
* Python dependency installation
* Docker Compose configuration

---

# Integration Testing

Location:

```text
integration-tests/test_system_integration.py
```

Current status:

```text
Placeholder implementation
```

Planned coverage:

* Backend health validation
* PostgreSQL connectivity
* Redis connectivity
* AI/ML availability
* Frontend ↔ Backend integration
* Backend ↔ AI/ML integration

---

# OpenAPI Documentation

Location:

```text
openapi_spec.yaml
```

Current status:

```text
Placeholder specification
```

To be updated as API contracts are finalized.
