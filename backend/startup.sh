#!/bin/bash
# Azure App Service startup script for VibeDocs backend

echo "Starting VibeDocs Backend..."
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"

# Run migrations (skip if database not configured)
if [ -n "$DATABASE_URL" ]; then
    echo "Running database migrations..."
    alembic upgrade head || echo "Warning: Migration failed, continuing anyway..."
else
    echo "DATABASE_URL not set, skipping migrations"
fi

# Start the application with Gunicorn
echo "Starting Gunicorn server..."
gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
