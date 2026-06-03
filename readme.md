# SuRaksha Setu - DevOps & Infrastructure Documentation

## Project Overview

SuRaksha Setu is a multi-service banking security platform being developed using separate team branches for Backend, Frontend, AI/ML, and DevOps.

This branch (`devops-amrita`) contains the infrastructure setup required to deploy and integrate all services once development is completed.

The goal of this branch is to provide:

* Environment management
* Docker-based deployment
* Secrets management
* Service orchestration
* Integration testing support

---

# Team Structure

## Backend Team

Responsible for:

* Spring Boot API
* Authentication
* Database interaction
* WebSocket communication
* Business logic

Expected service:

```text
Spring Boot Application
```

---

## Frontend Team

Responsible for:

* User Interface
* Dashboard
* Authentication Screens
* Real-time Monitoring

Expected service:

```text
Next.js / Flutter Frontend
```

---

## AI/ML Team

Responsible for:

* Behavioral Analytics
* Fraud Detection
* Risk Scoring
* Document Analysis

Expected service:

```text
Python / FastAPI Service
```

---

## DevOps Team

Responsible for:

* Docker configuration
* Environment variables
* Deployment automation
* Secrets generation
* Integration support

---

# Current Repository Structure

```text
SuRaksha-Setu/
│
├── .github/
│
├── admin-dashboard/
│
├── infra/
│   ├── docker-compose.yml
│   ├── .env.example
│   ├── setup_secrets.sh
│   └── prometheus.yml
│
├── integration-tests/
│
├── Makefile
├── openapi_spec.yaml
└── README.md
```

---

# Infrastructure Folder Explanation

The entire deployment configuration is stored inside:

```text
infra/
```

This folder contains all files needed to start and configure project services.

---

## docker-compose.yml

Purpose:

Manage and run all services using a single command.

Services configured:

### PostgreSQL

Stores:

* User data
* Transactions
* Fraud reports
* Application records

Port:

```text
5432
```

---

### Redis

Used for:

* Caching
* Session storage
* Rate limiting
* Temporary data

Port:

```text
6379
```

---

### Backend Service

Reserved for:

```text
Spring Boot Application
```

Responsibilities:

* Authentication
* API handling
* Database communication

---

### AI/ML Service

Reserved for:

```text
Python / FastAPI Service
```

Responsibilities:

* Risk scoring
* Behavioral analytics
* Fraud detection

---

### Dashboard

Reserved for:

```text
Admin Dashboard
```

Responsibilities:

* Display risk scores
* Monitoring
* System administration

---

# Environment Variables

## Why Environment Variables?

Sensitive information should never be hardcoded.

Examples:

* Database passwords
* JWT secrets
* API endpoints

Environment variables allow different developers to use different values without modifying source code.

---

# .env.example

File:

```text
infra/.env.example
```

Purpose:

Template for developers.

Before running the project:

```bash
cp infra/.env.example infra/.env
```

and update values.

---

## Variable Explanation

### PostgreSQL

```env
POSTGRES_DB
```

Database name.

---

```env
POSTGRES_USER
```

Database username.

---

```env
POSTGRES_PASSWORD
```

Database password.

---

### Backend Database Connection

```env
DB_HOST
```

Database host.

---

```env
DB_PORT
```

Database port.

---

### Redis

```env
REDIS_HOST
```

Redis server host.

---

```env
REDIS_PORT
```

Redis server port.

---

### Security

```env
JWT_SECRET
```

Secret key used for JWT token generation and validation.

Must never be committed to GitHub.

---

### Frontend

```env
NEXT_PUBLIC_API_URL
```

Backend API URL used by the dashboard.

---

### Ports

```env
SPRING_PORT
```

Backend port.

---

```env
FASTAPI_PORT
```

AI/ML service port.

---

```env
NEXT_PORT
```

Dashboard port.

---

# setup_secrets.sh

Purpose:

Generate configuration files automatically from environment variables.

This prevents developers from manually creating configuration files.

---

## Backend Configuration Generated

File:

```text
src/main/resources/application-prod.yml
```

Generated values:

* PostgreSQL connection
* Redis connection
* JWT secret

Used during production deployment.

---

## AI/ML Configuration Generated

File:

```text
aiml.env
```

Contains:

* Database credentials
* Redis credentials
* JWT configuration

This file can later be imported into the final AI/ML service.

---

# Makefile

Purpose:

Provide simple commands for developers.

Instead of:

```bash
docker compose -f infra/docker-compose.yml up -d
```

developers can run:

```bash
make up
```

---

## Available Commands

### Build Services

```bash
make build
```

Build and start all containers.

---

### Start Services

```bash
make up
```

Start containers.

---

### Stop Services

```bash
make down
```

Stop containers.

---

### Restart Services

```bash
make restart
```

Restart containers.

---

### View Logs

```bash
make logs
```

Show live container logs.

---

### List Containers

```bash
make ps
```

Display running containers.

---

### Cleanup

```bash
make clean
```

Remove containers, networks and unused Docker resources.

---

# Deployment Workflow

When all branches are merged:

```text
Backend
     +
Frontend
     +
AI/ML
     +
DevOps
     ↓
Integration Branch
     ↓
Main Branch
```

Expected deployment flow:

```text
1. Configure .env
2. Generate secrets
3. Build services
4. Start Docker containers
5. Verify health checks
6. Run integration tests
7. Deploy
```

---

# Current Status

## Completed

* Docker Compose setup
* Environment variable template
* Secrets generation script
* Makefile automation
* Service definitions
* Integration test structure

## Pending

* Backend integration
* AI/ML integration
* Frontend integration
* Final deployment validation

---

# Maintainer

### DevOps & Infrastructure

Amrita Neogi

Responsible for:

* Deployment
* Docker
* Environment Management
* Secrets Management
* Integration Support
