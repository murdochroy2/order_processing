# E-commerce Backend Order Processing System

This is a Django-based backend system for processing e-commerce orders asynchronously.

## Prerequisites

- Docker and Docker Compose installed on your system
  - Docker Desktop. [Install Docker](https://docs.docker.com/get-docker/)
  - Docker Compose. [Install Docker Compose](https://docs.docker.com/compose/install/)

## Running with Docker

1. Clone the repository
   ```bash
   git clone https://github.com/murdochroy2/order_processing.git
   cd ecommerce_backend
   ```
2. Build and start the containers:
   ```bash
   docker compose up --build
   ```
   This will start both the Django application and PostgreSQL database.

3. The API will be available at http://localhost:8000/api/

## API Endpoints

### Postman Collection (Recommended)
Use the [Ecommerce API.postman_collection.json](./Ecommerce%20API.postman_collection.json) file to import the API endpoints into Postman. This file is included in the repository.

### Get All Orders

```bash
curl http://localhost:8000/api/orders/
```

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

## Running Tests

```bash
docker compose run --rm test
```

## Running Load Tests
To simulate 1000 users making concurrent requests per second for 30 seconds, run the following below. First ensure that the docker compose is running:
```bash
docker compose up
```
Then run the following command:
```bash
docker compose exec web locust \
    --headless \
    --users 1000 \
    --spawn-rate 1000 \
    --run-time 30s \
    --csv=locust_results \
    --host http://localhost:8000
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

## Assumptions

1. Order IDs are unique and provided by the client
2. The system runs on a single instance (for simplicity)
3. No authentication/authorization implemented
4. In-memory queue means orders might be lost if server crashes

## Limitations and Possible Improvements

1. Replace in-memory queue with Redis or RabbitMQ for persistence
2. Implement proper error handling and retries
4. Implement horizontal scaling capabilities

## Docker Configuration

The application is containerized using Docker and includes:
- Django application running with Gunicorn
- PostgreSQL database
- Automatic migrations on startup
- Volume persistence for the database

To rebuild the containers:

```bash
docker compose down
docker compose up --build
```
