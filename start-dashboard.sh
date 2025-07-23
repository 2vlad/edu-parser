#!/bin/bash

# Start script for the Edu Parser Dashboard
# This script can be used for local development or production deployment

echo "🔍 DEBUG: Starting start-dashboard.sh script"
echo "🔍 DEBUG: Script arguments: $@"
echo "🔍 DEBUG: Current working directory: $(pwd)"
echo "🔍 DEBUG: User: $(whoami)"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "🔍 DEBUG: Loaded .env file"
else
    echo "🔍 DEBUG: No .env file found"
fi

# Detailed PORT debugging
echo "🔍 DEBUG: Raw PORT variable before processing: '$PORT'"
echo "🔍 DEBUG: PORT type check:"
if [ -z "$PORT" ]; then
    echo "🔍 DEBUG: PORT is empty/unset"
elif [ "$PORT" = "\$PORT" ]; then
    echo "🚨 DEBUG: PORT contains literal '\$PORT' string!"
elif [ "$PORT" = '$PORT' ]; then
    echo "🚨 DEBUG: PORT contains literal '\$PORT' string (single quotes)!"
else
    echo "🔍 DEBUG: PORT appears to have a value: '$PORT'"
fi

# Set default values if not provided
# Railway provides PORT, but sometimes it's empty during cron runs
if [ -z "$PORT" ] || [ "$PORT" = "\$PORT" ] || [ "$PORT" = '$PORT' ]; then
    export PORT=8080
    echo "🔍 DEBUG: Set PORT to default: $PORT"
else
    echo "🔍 DEBUG: Using existing PORT: $PORT"
fi

export FLASK_DEBUG=${FLASK_DEBUG:-false}

echo "🔍 DEBUG: Final PORT value: $PORT"
echo "🔍 DEBUG: Final FLASK_DEBUG value: $FLASK_DEBUG"
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
        --bind "0.0.0.0:${PORT}" \
        --workers $WORKERS \
        --worker-class sync \
        --timeout 120 \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        dashboard:app
fi