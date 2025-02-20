from locust import HttpUser, task, between
import uuid
import random
import logging

# Configure logging
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoadTestUser(HttpUser):
    host = "http://127.0.0.1:8000"  # Change this to your API host

    @task
    def create_order(self):
        data = {
            "user_id": random.randint(1, 1000),
            "order_id": str(uuid.uuid4()),
            "item_ids": [random.randint(1000, 2000) for _ in range(random.randint(1, 5))],
            "total_amount": round(random.uniform(10, 500), 2),
        }
        headers = {"Content-Type": "application/json"}

        with self.client.post("/api/orders/", json=data, headers=headers, catch_response=True) as response:
            if response.status_code != 201:  # Adjust based on expected status code
                response.failure(f"Failed! Status: {response.status_code}, ") # Response: {response.text}
                # logger.error(f"Request Failed: {data} | Response: {response.status_code} - {response.text}")
            else:
                response.success()
