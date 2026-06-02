#!/bin/bash

set -e

echo "Initializing SuRaksha Setu production secrets..."

required_vars=(
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
DB_HOST
DB_PORT
JWT_SECRET
REDIS_HOST
REDIS_PORT
)

for var in "${required_vars[@]}"
do
    if [ -z "${!var}" ]; then
        echo "ERROR: $var is not set"
        exit 1
    fi
done

# ======================================
# Backend Spring Boot Production Config
# ======================================

mkdir -p ../src/main/resources

cat > ../src/main/resources/application-prod.yml <<EOF
spring:
  datasource:
    url: jdbc:postgresql://${DB_HOST}:${DB_PORT}/${POSTGRES_DB}
    username: ${POSTGRES_USER}
    password: ${POSTGRES_PASSWORD}
    driver-class-name: org.postgresql.Driver

  data:
    redis:
      host: ${REDIS_HOST}
      port: ${REDIS_PORT}

security:
  jwt:
    secret: ${JWT_SECRET}
EOF

# ======================================
# Generic AI/ML Environment File
# ======================================

cat > ../aiml.env <<EOF
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}

POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

REDIS_HOST=${REDIS_HOST}
REDIS_PORT=${REDIS_PORT}

JWT_SECRET=${JWT_SECRET}
EOF

echo "Backend production configuration generated successfully."
echo "AI/ML environment file generated successfully (aiml.env)."