#!/bin/sh
# Run Alembic migrations then start the application server.
set -e

echo "Running database migrations..."
alembic -c /app/alembic.ini upgrade head

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
