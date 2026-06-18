# Deployment Plan

## Services

### PostgreSQL

Port: 5432

### Redis

Port: 6379

### Spring Boot Backend

Port: 8080

### FastAPI ML Service

Port: 8000

### Dashboard

Port: 3000

---

## Network

Bridge Network:

suraksha-network

---

## Service Flow

Flutter
↓
Spring Boot
↓
PostgreSQL

Spring Boot
↓
Redis

Spring Boot
↓
FastAPI ML Service

Dashboard
↓
Spring Boot

---

## Environment Variables

POSTGRES_DB

POSTGRES_USER

POSTGRES_PASSWORD

JWT_SECRET

REDIS_HOST

REDIS_PORT

AI_SERVICE_URL

SPRING_PORT

FASTAPI_PORT

NEXT_PORT

---

## Future Docker Compose

postgres

redis

backend

ml-service

dashboard
