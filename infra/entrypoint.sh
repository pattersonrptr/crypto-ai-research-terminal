#!/bin/sh
# Run Alembic migrations, optionally seed data, then start the application server.
set -e

echo "Running database migrations..."
alembic -c /app/alembic.ini upgrade head

# Only seed when AUTO_SEED is explicitly set to "true" (default: false)
if [ "${AUTO_SEED}" = "true" ]; then
    echo "AUTO_SEED=true — seeding database..."
    python -m scripts.seed_data || echo "Seed script failed (non-fatal), continuing..."
else
    echo "AUTO_SEED is not 'true' — skipping seed. Use 'cryptoai seed' to seed manually."
fi

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
