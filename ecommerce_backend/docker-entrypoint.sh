#!/bin/bash

# Wait for database
echo "Waiting for database..."
sleep 5

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Start server
echo "Starting server..."
gunicorn ecommerce_backend.wsgi:application --bind 0.0.0.0:8000 --access-logfile - --reload