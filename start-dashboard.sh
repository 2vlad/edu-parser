#!/bin/bash

# Start script for the Edu Parser Dashboard
# This script can be used for local development or production deployment

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set default values if not provided
export PORT=${PORT:-5000}
export FLASK_DEBUG=${FLASK_DEBUG:-false}

echo "Starting Edu Parser Dashboard..."
echo "Port: $PORT"
echo "Debug mode: $FLASK_DEBUG"

if [ "$FLASK_DEBUG" = "true" ]; then
    # Development mode - use Flask's built-in server
    echo "Running in development mode"
    python dashboard.py
else
    # Production mode - use Gunicorn
    echo "Running in production mode with Gunicorn"
    
    # Calculate workers based on CPU cores
    WORKERS=${DASHBOARD_WORKERS:-$(python -c "import multiprocessing; print(multiprocessing.cpu_count() * 2 + 1)")}
    
    echo "Workers: $WORKERS"
    
    gunicorn \
        --bind 0.0.0.0:$PORT \
        --workers $WORKERS \
        --worker-class sync \
        --timeout 120 \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        dashboard:app
fi