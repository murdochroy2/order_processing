from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Order, OrderStatus

class OrderViewTests(TransactionTestCase):
    def setUp(self):
        self.client = APIClient()
        # Create some test orders
        self.order1 = Order.objects.create(
            order_id="ORD001",
            user_id="USR001",
            item_ids=["ITEM001", "ITEM002"],
            total_amount=99.99,
            status=OrderStatus.PENDING
        )
        self.order2 = Order.objects.create(
            order_id="ORD002",
            user_id="USR002",
            item_ids=["ITEM003"],
            total_amount=149.99,
            status=OrderStatus.PROCESSING
        )
        self.order3 = Order.objects.create(
            order_id="ORD003",
            user_id="USR003",
            item_ids=["ITEM004", "ITEM005", "ITEM006"],
            total_amount=299.99,
            status=OrderStatus.COMPLETED
        )

    def test_get_all_orders(self):
        """Test retrieving all orders"""
        # Make GET request to orders endpoint
        url = reverse('orders-list')  # Make sure this matches your URL configuration
        response = self.client.get(url)

        # Check that the request was successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that we got all orders in the response
        self.assertEqual(len(response.data), 3)
        
        # Verify the content of the response
        order_ids = {order['order_id'] for order in response.data}
        expected_ids = {str(self.order1.order_id), 
                       str(self.order2.order_id), 
                       str(self.order3.order_id)}
        self.assertEqual(order_ids, expected_ids)

    def test_get_order_by_id(self):
        """Test retrieving a single order by ID"""
        # Make GET request to order detail endpoint
        url = reverse('order-detail', args=[self.order1.order_id])
        response = self.client.get(url)

        # Check that the request was successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify the content of the response
        self.assertEqual(response.data['order_id'], str(self.order1.order_id))
        self.assertEqual(response.data['user_id'], self.order1.user_id)
        self.assertEqual(str(response.data['total_amount']), str(self.order1.total_amount))
        self.assertEqual(response.data['status'], self.order1.status)
        self.assertEqual(response.data['item_ids'], self.order1.item_ids)

    def test_get_nonexistent_order(self):
        """Test retrieving an order that doesn't exist"""
        url = reverse('order-detail', args=['NONEXISTENT'])
        response = self.client.get(url)

        # Check that the request returns 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
