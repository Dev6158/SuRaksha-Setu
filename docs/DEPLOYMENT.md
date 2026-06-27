# SuRaksha-Setu Deployment Guide

## Overview

SuRaksha-Setu is a fraud detection and document verification platform composed of multiple containerized services orchestrated using Docker Compose.

The system consists of:

* **Admin Dashboard** (Next.js)
* **Backend API** (Spring Boot)
* **ML Service** (FastAPI)
* **PostgreSQL Database**
* **Redis Cache**

All services communicate through a dedicated Docker network and can be started with a single command.

---

# System Architecture

```text
┌─────────────────────┐
│  Admin Dashboard    │
│      Next.js        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Spring Boot API   │
└───────┬─────┬───────┘
        │     │
        │     ▼
        │  Redis
        │
        ▼
   PostgreSQL

        │
        ▼

┌─────────────────────┐
│  ML Service         │
│  FastAPI + AI/ML    │
└─────────────────────┘
```

---

# Service Ports

| Service         | Port |
| --------------- | ---- |
| Admin Dashboard | 3000 |
| Backend API     | 8080 |
| ML Service      | 8000 |
| PostgreSQL      | 5432 |
| Redis           | 6379 |

---

# Prerequisites

Before deployment, ensure the following tools are installed:

* Docker Desktop
* Docker Compose
* Git

Verify installation:

```bash
docker --version
docker compose version
git --version
```

---

# Environment Configuration

Create or update the environment file:

```text
infra/.env
```

Example configuration:

```env
POSTGRES_DB=suraksha
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change_me

DB_HOST=postgres
DB_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379

SPRING_PORT=8080
FASTAPI_PORT=8000
NEXT_PORT=3000
```

---

# Starting the Application

Build and start all services:

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

Verify running containers:

```bash
docker compose -f infra/docker-compose.yml ps
```

Expected services:

```text
suraksha-dashboard
suraksha-backend
suraksha-ml
suraksha-postgres
suraksha-redis
```

---

# Accessing Services

### Dashboard

```text
http://localhost:3000
```

### Backend API

```text
http://localhost:8080
```

### Swagger Documentation

```text
http://localhost:8080/swagger-ui/index.html
```

### OpenAPI Specification

```text
http://localhost:8080/v3/api-docs
```

### ML Service Health Endpoint

```text
http://localhost:8000/healthz
```

---

# Health Verification

Check container status:

```bash
docker compose -f infra/docker-compose.yml ps
```

A healthy deployment should show:

```text
backend      healthy
ml-service   healthy
postgres     healthy
redis        healthy
dashboard    running
```

---

# Viewing Logs

View logs for all services:

```bash
docker compose -f infra/docker-compose.yml logs -f
```

View logs for a specific service:

```bash
docker logs suraksha-backend
docker logs suraksha-ml
docker logs suraksha-dashboard
```

---

# Running Integration Tests

Execute the integration test suite:

```bash
py -m pytest integration-tests -v
```

Expected result:

```text
14 passed
```

---

# Rebuilding Services

Rebuild all containers:

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

Rebuild a specific service:

```bash
docker compose -f infra/docker-compose.yml build dashboard --no-cache
docker compose -f infra/docker-compose.yml up -d dashboard
```

---

# Stopping the Application

Stop all services:

```bash
docker compose -f infra/docker-compose.yml down
```

Stop and remove volumes:

```bash
docker compose -f infra/docker-compose.yml down -v
```

---

# Troubleshooting

## Dashboard Not Loading

Check:

```bash
docker logs suraksha-dashboard
```

Verify:

```text
http://localhost:3000
```

is reachable.

---

## Backend Unhealthy

Check:

```bash
docker logs suraksha-backend
```

Verify database and Redis connectivity.

---

## ML Service Unhealthy

Check:

```bash
docker logs suraksha-ml
```

Verify:

```text
http://localhost:8000/healthz
```

returns:

```json
{
  "status": "ok"
}
```

---

## Database Connection Issues

Verify PostgreSQL container:

```bash
docker ps
```

Check credentials in:

```text
infra/.env
```

---

# Deployment Status

Current deployment validation:

* Dashboard containerized and operational
* Backend API healthy
* ML Service healthy
* PostgreSQL healthy
* Redis healthy
* Docker Compose orchestration validated
* Integration tests passing
* Ready for team review and deployment

---

**Project:** SuRaksha-Setu
**Environment:** Development / Integration Testing
**Maintained By:** DevOps & Dashboard Team
