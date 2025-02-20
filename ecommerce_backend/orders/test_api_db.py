from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
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

    def test_create_order(self):
        """Test creating a new order via POST request"""
        # Prepare test data
        order_data = {
            'order_id': 'ORD004',
            'user_id': 'USR004',
            'item_ids': ['ITEM007', 'ITEM008'],
            'total_amount': 199.99,
        }

        # Make POST request to create order
        url = reverse('orders-list')
        response = self.client.post(url, order_data, format='json')

        # Check that the request was successful
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify the order was created in the database
        created_order = Order.objects.get(order_id='ORD004')
        self.assertEqual(created_order.user_id, 'USR004')
        self.assertEqual(created_order.total_amount, Decimal('199.99'))
        self.assertEqual(created_order.item_ids, ['ITEM007', 'ITEM008'])

        # Verify the response data matches the created order
        self.assertEqual(response.data['order_id'], order_data['order_id'])
        self.assertEqual(response.data['user_id'], order_data['user_id'])
        self.assertEqual(float(response.data['total_amount']), order_data['total_amount'])
        self.assertEqual(response.data['status'], OrderStatus.PENDING)
        self.assertEqual(response.data['item_ids'], order_data['item_ids'])

    def test_create_invalid_order(self):
        """Test creating an order with invalid data"""
        # Prepare invalid test data (missing required fields)
        invalid_order_data = {
            'order_id': 'ORD005'
            # Missing other required fields
        }

        # Make POST request with invalid data
        url = reverse('orders-list')
        response = self.client.post(url, invalid_order_data, format='json')

        # Check that the request was unsuccessful
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Verify the order was not created in the database
        with self.assertRaises(Order.DoesNotExist):
            Order.objects.get(order_id='ORD005')

class OrderDatabaseTests(TestCase):
    def setUp(self):
        # Create test orders directly in the database
        self.order1 = Order.objects.create(
            order_id="DB-TEST-001",
            user_id="USER-001",
            item_ids=[1, 2],
            total_amount=199.99,
            status=OrderStatus.PENDING
        )
        self.order2 = Order.objects.create(
            order_id="DB-TEST-002",
            user_id="USER-002",
            item_ids=[3],
            total_amount=299.99,
            status=OrderStatus.COMPLETED,
            processing_started_at=timezone.now() - timedelta(minutes=5),
            processing_completed_at=timezone.now()
        )

    def test_create_order(self):
        order = Order.objects.create(
            order_id="DB-TEST-003",
            user_id="USER-003",
            item_ids=[4, 5],
            total_amount=399.99
        )
        self.assertEqual(order.order_id, "DB-TEST-003")
        self.assertEqual(order.status, OrderStatus.PENDING)
        self.assertEqual(order.item_ids, [4, 5])

    def test_update_order_status(self):
        self.order1.status = OrderStatus.PROCESSING
        self.order1.processing_started_at = timezone.now()
        self.order1.save()

        updated_order = Order.objects.get(order_id="DB-TEST-001")
        self.assertEqual(updated_order.status, OrderStatus.PROCESSING)
        self.assertIsNotNone(updated_order.processing_started_at)

    def test_order_completion(self):
        now = timezone.now()
        self.order1.status = OrderStatus.COMPLETED
        self.order1.processing_started_at = now - timedelta(minutes=3)
        self.order1.processing_completed_at = now
        self.order1.save()

        completed_order = Order.objects.get(order_id="DB-TEST-001")
        self.assertEqual(completed_order.status, OrderStatus.COMPLETED)
        self.assertIsNotNone(completed_order.processing_completed_at)
        
        # Test processing duration
        processing_time = completed_order.processing_completed_at - completed_order.processing_started_at
        self.assertEqual(processing_time.total_seconds(), 180)  # 3 minutes = 180 seconds

    def test_order_filtering(self):
        # Test filtering by status
        completed_orders = Order.objects.filter(status=OrderStatus.COMPLETED)
        self.assertEqual(completed_orders.count(), 1)
        self.assertEqual(completed_orders.first().order_id, "DB-TEST-002")

        # Test filtering by user_id
        user_orders = Order.objects.filter(user_id="USER-001")
        self.assertEqual(user_orders.count(), 1)
        self.assertEqual(user_orders.first().order_id, "DB-TEST-001")
