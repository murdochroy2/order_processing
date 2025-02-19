from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Order, OrderStatus
import json

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
