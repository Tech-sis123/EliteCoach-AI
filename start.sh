#!/bin/bash
set -euo pipefail

# Run migrations/database patches
echo "Running database migrations..."
python migrate_v1.py

# Start the application
echo "Starting Gunicorn..."
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
