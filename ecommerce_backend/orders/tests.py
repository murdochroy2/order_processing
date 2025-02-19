from django.test import TransactionTestCase  # Changed from TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Order, OrderStatus
from django.db import connections
from functools import wraps
from django.test.utils import override_settings
import concurrent.futures
import time

def close_old_connections(func):
    """Decorator to handle database connections"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        connections.close_all()
        result = func(*args, **kwargs)
        connections.close_all()
        return result
    return wrapper

class OrderTests(TransactionTestCase):  # Changed to TransactionTestCase
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.order_data = {
            'order_id': 'TEST001',
            'user_id': 'USER001',
            'item_ids': [1, 2, 3],
            'total_amount': '99.99'
        }

    def test_create_order(self):
        response = self.client.post(
            '/api/orders/',
            self.order_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.get().status, OrderStatus.PENDING)

    def test_get_metrics(self):
        Order.objects.create(**self.order_data)
        
        response = self.client.get('/api/orders/metrics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['total_orders'], 1)
        self.assertEqual(data['status_counts'][OrderStatus.PENDING], 1)

    @override_settings(DATABASE_CONNECTIONS_TTL=0)
    def test_concurrent_requests(self):
        """Test the system with concurrent order creation requests"""
        NUM_REQUESTS = 1000
        MAX_WORKERS = 50  # Reduced from 32 to prevent connection issues
        results = []
        start_time = time.time()

        @close_old_connections
        def create_order(i):
            try:
                client = APIClient()
                order_data = {
                    'order_id': f'TEST{i:04d}',
                    'user_id': f'USER{i:04d}',
                    'item_ids': [1, 2, 3],
                    'total_amount': '99.99'
                }
                
                response = client.post('/api/orders/', order_data, format='json')
                return {
                    'status_code': response.status_code,
                    'order_id': order_data['order_id']
                }
            except Exception as e:
                return {
                    'status_code': 500,
                    'error': str(e),
                    'order_id': order_data['order_id']
                }

        # Use ThreadPoolExecutor with smaller batch sizes
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit requests in batches to prevent overwhelming the database
            batch_size = 100
            for batch_start in range(0, NUM_REQUESTS, batch_size):
                batch_end = min(batch_start + batch_size, NUM_REQUESTS)
                batch_futures = [
                    executor.submit(create_order, i) 
                    for i in range(batch_start, batch_end)
                ]
                
                for future in concurrent.futures.as_completed(batch_futures):
                    results.append(future.result())

        end_time = time.time()
        
        # Analyze results
        successful_requests = sum(1 for r in results if r['status_code'] == status.HTTP_201_CREATED)
        failed_requests = len(results) - successful_requests
        
        # Get actual orders in database
        total_orders = Order.objects.count()
        
        # Detailed test report
        print(f"\nConcurrent Request Test Results:")
        print(f"Total requests attempted: {NUM_REQUESTS}")
        print(f"Successful requests: {successful_requests}")
        print(f"Failed requests: {failed_requests}")
        print(f"Total orders in database: {total_orders}")
        print(f"Total time: {end_time - start_time:.2f} seconds")
        print(f"Average time per request: {(end_time - start_time) / NUM_REQUESTS:.4f} seconds")
        
        if failed_requests > 0:
            print("\nFailed request details:")
            for result in results:
                if result['status_code'] != status.HTTP_201_CREATED:
                    print(f"Order ID: {result['order_id']}, Error: {result.get('error', 'Unknown error')}")

        # Assertions
        self.assertGreater(successful_requests, 0, "No requests were successful")
        self.assertEqual(total_orders, successful_requests, 
                        "Number of orders in database doesn't match successful requests")
        self.assertLess(failed_requests / NUM_REQUESTS, 0.1, 
                        "Error rate exceeded 10%")

    @override_settings(DATABASE_CONNECTIONS_TTL=0)
    def test_concurrent_metrics_access(self):
        """Test concurrent access to metrics endpoint"""
        NUM_REQUESTS = 1000
        MAX_WORKERS = 50
        
        # Create test orders first
        test_orders = 100
        order_objects = [
            Order(
                order_id=f'METRIC{i:04d}',
                user_id=f'USER{i:04d}',
                item_ids=[1, 2, 3],
                total_amount='99.99',
                status=OrderStatus.PENDING
            ) for i in range(test_orders)
        ]
        Order.objects.bulk_create(order_objects)
        
        @close_old_connections
        def get_metrics():
            try:
                client = APIClient()
                response = client.get('/api/orders/metrics/')
                return {
                    'status_code': response.status_code,
                    'data': response.json() if response.status_code == status.HTTP_200_OK else None
                }
            except Exception as e:
                return {'status_code': 500, 'error': str(e)}

        start_time = time.time()
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(get_metrics) for _ in range(NUM_REQUESTS)]
            
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        end_time = time.time()
        
        # Analyze results
        successful_requests = sum(1 for r in results if r['status_code'] == status.HTTP_200_OK)
        failed_requests = len(results) - successful_requests
        
        print(f"\nConcurrent Metrics Test Results:")
        print(f"Total requests attempted: {NUM_REQUESTS}")
        print(f"Successful requests: {successful_requests}")
        print(f"Failed requests: {failed_requests}")
        print(f"Total time: {end_time - start_time:.2f} seconds")
        print(f"Average time per request: {(end_time - start_time) / NUM_REQUESTS:.4f} seconds")
        
        if failed_requests > 0:
            print("\nFailed request details:")
            for result in results:
                if result['status_code'] != status.HTTP_200_OK:
                    print(f"Error: {result.get('error', 'Unknown error')}")

        self.assertGreater(successful_requests, 0, "No requests were successful")
        self.assertLess(failed_requests / NUM_REQUESTS, 0.1, 
                        "Error rate exceeded 10%")