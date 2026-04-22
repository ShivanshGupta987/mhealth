#!/bin/bash
set -e

echo "========================================="
echo "mHealth Backend Starting..."
echo "Service Type: ${SERVICE_TYPE:-api}"
echo "========================================="

# Function to wait for PostgreSQL
wait_for_postgres() {
    echo "Waiting for PostgreSQL..."
    until pg_isready -h postgres -p 5432 -U postgres; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
    done
    echo "✓ PostgreSQL is ready!"
}

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    alembic upgrade head
    echo "✓ Migrations completed!"
}

# If API service, wait for DB and run migrations
if [ "${SERVICE_TYPE}" = "api" ]; then
    wait_for_postgres
    run_migrations
    
    echo "Starting FastAPI server on port 8000..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-*}"

# If Celery worker, wait for DB (no migrations needed)
elif [ "${SERVICE_TYPE}" = "celery_worker" ]; then
    wait_for_postgres
    
    # Also wait for backend API to be healthy
    echo "Waiting for Backend API to be ready..."
    until curl -f http://backend-api:8000/health > /dev/null 2>&1; do
        echo "Backend API is unavailable - sleeping"
        sleep 3
    done
    echo "✓ Backend API is ready!"
    
    echo "Starting Celery worker..."
    exec celery -A app.twilio.celery_config_twilio.celery_app worker -l info

elif [ "${SERVICE_TYPE}" = "celery_beat" ]; then
    wait_for_postgres
    echo "Starting Celery beat..."
    exec celery -A app.twilio.celery_config_twilio.celery_app beat -l info

# Default: API service
else
    wait_for_postgres
    run_migrations

    echo "Starting FastAPI server on port 8000 (default)..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-*}"
fi
