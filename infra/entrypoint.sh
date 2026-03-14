#!/bin/sh
# Run Alembic migrations, seed data, then start the application server.
set -e

echo "Running database migrations..."
alembic -c /app/alembic.ini upgrade head

echo "Seeding database (skips if data exists, backfills sub-scores if needed)..."
python -m scripts.seed_data || echo "Seed script failed (non-fatal), continuing..."

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
