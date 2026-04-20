#!/usr/bin/env bash
# start.sh - Starts the FastAPI server and (optionally) the Celery worker/beat.
# Usage:
#   ./start.sh           -> starts FastAPI only
#   ./start.sh worker    -> starts Celery worker only
#   ./start.sh beat      -> starts Celery beat only
set -e

ROLE="${1:-api}"

case "$ROLE" in
  api)
    echo "[twilio_service] Starting FastAPI server..."
    exec uvicorn app.main:app \
      --host "${TWILIO_SERVICE_HOST:-0.0.0.0}" \
      --port "${TWILIO_SERVICE_PORT:-8002}" \
      --log-level info
    ;;
  worker)
    echo "[twilio_service] Starting Celery worker..."
    exec celery -A app.celery_config_twilio.celery_app worker \
      --loglevel=info \
      --concurrency=4 \
      -Q twilio_calls,twilio_sentiment
    ;;
  beat)
    echo "[twilio_service] Starting Celery beat scheduler..."
    exec celery -A app.celery_config_twilio.celery_app beat \
      --loglevel=info \
      --scheduler celery.beat:PersistentScheduler
    ;;
  *)
    echo "Unknown role: $ROLE. Use api | worker | beat"
    exit 1
    ;;
esac
