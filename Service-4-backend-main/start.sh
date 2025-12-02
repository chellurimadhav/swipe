#!/bin/sh
# Startup script for Railway deployment
# Handles PORT environment variable properly

# Set default port if PORT is not set
if [ -z "$PORT" ]; then
    PORT=5000
fi

exec gunicorn --bind 0.0.0.0:"$PORT" --workers 4 --timeout 120 --access-logfile - --error-logfile - wsgi:app

