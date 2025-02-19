from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Order, OrderStatus
import json
import asyncio
import aiohttp
import concurrent.futures
import threading
from django.db import connection

class OrderTests(TestCase):
    def setUp(self):
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
        # Create a test order
        Order.objects.create(**self.order_data)
        
        response = self.client.get('/api/orders/metrics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['total_orders'], 1)
        self.assertEqual(data['status_counts'][OrderStatus.PENDING], 1)

    def test_concurrent_requests(self):
        """Test the system with 1000 concurrent order creation requests"""
        NUM_REQUESTS = 100
        successful_requests = 0
        failed_requests = 0
        
        def create_order(i):
            # Close old connections to avoid "Too many connections" error
            connection.close()
            
            client = APIClient()
            order_data = {
                'order_id': f'TEST{i:04d}',
                'user_id': f'USER{i:04d}',
                'item_ids': [1, 2, 3],
                'total_amount': '99.99'
            }
            
            response = client.post('/api/orders/', order_data, format='json')
            return response.status_code == status.HTTP_201_CREATED

        # Use ThreadPoolExecutor for concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
            futures = [executor.submit(create_order, i) for i in range(NUM_REQUESTS)]
            
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    successful_requests += 1
                else:
                    failed_requests += 1

        # Verify results
        total_orders = Order.objects.count()
        
        print(f"\nConcurrent request test results:")
        print(f"Successful requests: {successful_requests}")
        print(f"Failed requests: {failed_requests}")
        print(f"Total orders in database: {total_orders}")
        
        self.assertEqual(successful_requests, NUM_REQUESTS, 
                        "Not all requests were successful")
        self.assertEqual(total_orders, NUM_REQUESTS, 
                        "Number of orders in database doesn't match requests")

    def test_concurrent_metrics_access(self):
        """Test concurrent access to metrics endpoint with existing orders"""
        NUM_REQUESTS = 1000
        
        # Create test orders first
        for i in range(100):  # Create 100 test orders
            Order.objects.create(
                order_id=f'METRIC{i:04d}',
                user_id=f'USER{i:04d}',
                item_ids=[1, 2, 3],
                total_amount='99.99',
                status=OrderStatus.PENDING
            )
        
        def get_metrics():
            connection.close()  # Close old connections
            client = APIClient()
            response = client.get('/api/orders/metrics/')
            return response.status_code == status.HTTP_200_OK

        successful_requests = 0
        failed_requests = 0
        
        # Use ThreadPoolExecutor for concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
            futures = [executor.submit(get_metrics) for _ in range(NUM_REQUESTS)]
            
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    successful_requests += 1
                else:
                    failed_requests += 1

        print(f"\nConcurrent metrics test results:")
        print(f"Successful requests: {successful_requests}")
        print(f"Failed requests: {failed_requests}")
        
        self.assertEqual(successful_requests, NUM_REQUESTS, 
                        "Not all metrics requests were successful")
