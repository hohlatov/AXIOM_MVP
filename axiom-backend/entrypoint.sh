#!/bin/sh
set -e

echo "Applying database migrations..."
alembic upgrade head

echo "Seeding trainer tasks (idempotent)..."
python -m app.seed_tasks

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
