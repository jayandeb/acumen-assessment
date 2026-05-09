#!/bin/bash
set -e

echo "Running portfolio-service migrations..."
alembic upgrade head

echo "Starting portfolio-service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8001
