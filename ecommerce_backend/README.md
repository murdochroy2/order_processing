# E-commerce Backend Order Processing System

This is a Django-based backend system for processing e-commerce orders asynchronously.

## Running with Docker

1. Clone the repository
2. Build and start the containers:
   ```bash
   docker-compose up --build
   ```
   This will start both the Django application and PostgreSQL database.

3. The API will be available at http://localhost:8000/api/

## Running Locally (without Docker)

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
5. Start the server:
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Create Order 

```bash
curl -X POST http://localhost:8000/api/orders/ \
-H "Content-Type: application/json" \
-d '{
"order_id": "ORD001",
"user_id": "USER001",
"item_ids": [1, 2, 3],
"total_amount": 99.99
}'
```

### Check Order Status

```bash
curl http://localhost:8000/api/orders/ORD001/
```

### Get Metrics

```bash
curl http://localhost:8000/api/orders/metrics/
```

## Design Decisions

1. **Queue Implementation**: Used an in-memory queue with a singleton pattern to ensure single queue instance across the application.

2. **Database Design**: 
   - Used JSONField for item_ids to allow flexible item storage
   - Added timestamps for tracking processing time
   - Created indexes on frequently queried fields

3. **Asynchronous Processing**: 
   - Implemented using threading for simplicity
   - Queue processor runs in a separate daemon thread
   - Orders are processed one at a time with simulated processing time

## Assumptions

1. Order IDs are unique and provided by the client
2. Processing time is simulated (1-3 seconds)
3. The system runs on a single instance (for simplicity)
4. No authentication/authorization implemented
5. In-memory queue means orders might be lost if server crashes

## Limitations and Possible Improvements

1. Replace in-memory queue with Redis or RabbitMQ for persistence
2. Add authentication and authorization
3. Implement proper error handling and retries
4. Add more comprehensive metrics and monitoring
5. Implement horizontal scaling capabilities

## Docker Configuration

The application is containerized using Docker and includes:
- Django application running with Gunicorn
- PostgreSQL database
- Automatic migrations on startup
- Volume persistence for the database

To rebuild the containers:

```bash
docker-compose down
docker-compose up --build
```

To view logs:

```bash
docker-compose logs -f
```

This Docker configuration:
1. Uses PostgreSQL instead of SQLite for better performance
2. Runs the Django application with Gunicorn for production-grade serving
3. Includes automatic database migrations on startup
4. Persists database data using Docker volumes
5. Provides proper environment variable configuration
6. Uses a slim Python base image to minimize container size

To run the application:
1. Make sure Docker and Docker Compose are installed
2. Navigate to the project directory
3. Run `docker-compose up --build`
4. Access the API at http://localhost:8000/api/

The application will automatically handle database migrations and start the server.