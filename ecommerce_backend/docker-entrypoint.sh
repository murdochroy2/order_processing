#!/bin/bash

# Wait for database
echo "Waiting for database..."
sleep 5

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Check if orders table is empty and populate sample data if it is
echo "Checking if database needs sample data..."

ORDER_COUNT=$(python manage.py shell -c "from orders.models import Order; print(Order.objects.count())")
if [ "$ORDER_COUNT" -eq "0" ]; then
    echo "Populating sample data..."
    python manage.py populate_sample_data --count 50
    echo "Sample data populated successfully!"
fi

# Start server
echo "Starting server..."
gunicorn ecommerce_backend.wsgi:application --bind 0.0.0.0:8000 --access-logfile - --reload