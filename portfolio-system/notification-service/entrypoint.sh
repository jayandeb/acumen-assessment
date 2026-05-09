#!/bin/bash
set -e

echo "Running notification-service migrations..."
alembic upgrade head

echo "Starting notification-service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8002
