from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from datetime import timedelta
import time

from .models import Order, OrderStatus
from .queue_manager import OrderQueue

class OrderQueueTests(TransactionTestCase):
    def setUp(self):
        self.queue_manager = OrderQueue()
        self.queue_manager.start_processing()

    def test_order_processing_flow(self):
        # Create a test order
        order = Order.objects.create(
            order_id="QUEUE-TEST-001",
            user_id="USER-001",
            item_ids=[1, 2],
            total_amount=199.99
        )
        
        # Add order to queue
        self.queue_manager.add_order(order)
        
        # Wait for processing to complete (with timeout)
        max_wait = 5  # seconds
        start_time = time.time()
        while time.time() - start_time < max_wait:
            # order.refresh_from_db()
            if order.status == OrderStatus.COMPLETED:
                break
            time.sleep(0.1)
        
        # Verify order was processed
        self.assertEqual(order.status, OrderStatus.COMPLETED)
        self.assertIsNotNone(order.processing_started_at)
        self.assertIsNotNone(order.processing_completed_at)
        self.assertTrue(order.processing_completed_at > order.processing_started_at)

    def test_multiple_orders_processing(self):
        # Create multiple test orders
        orders = []
        for i in range(3):
            order = Order.objects.create(
                order_id=f"QUEUE-TEST-{i+1}",
                user_id=f"USER-{i+1}",
                item_ids=[i+1],
                total_amount=99.99 * (i+1)
            )
            orders.append(order)
            self.queue_manager.add_order(order)
        
        # Wait for all orders to be processed
        time.sleep(5)
        
        # Verify all orders were processed
        for order in orders:
            order.refresh_from_db()
            self.assertEqual(order.status, OrderStatus.COMPLETED)
            self.assertIsNotNone(order.processing_started_at)
            self.assertIsNotNone(order.processing_completed_at)

    def test_queue_manager_singleton(self):
        # Test that OrderQueue is a singleton
        queue_manager2 = OrderQueue()
        self.assertEqual(id(self.queue_manager), id(queue_manager2))
        
        # Test that the queue is shared
        order = Order.objects.create(
            order_id="QUEUE-TEST-SINGLETON",
            user_id="USER-001",
            item_ids=[1],
            total_amount=99.99
        )
        
        queue_manager2.add_order(order)
        time.sleep(2)
        
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.COMPLETED)

    def test_stop_and_restart_processing(self):
        # Create an order
        order1 = Order.objects.create(
            order_id="QUEUE-TEST-STOP",
            user_id="USER-001",
            item_ids=[1],
            total_amount=99.99
        )
        
        # Stop processing
        self.queue_manager.stop_processing()
        
        # Add order to queue
        self.queue_manager.add_order(order1)
        time.sleep(1)
        
        # Verify order hasn't been processed
        order1.refresh_from_db()
        self.assertEqual(order1.status, OrderStatus.PENDING)
        
        # Restart processing
        self.queue_manager.start_processing()
        time.sleep(2)
        
        # Verify order has been processed
        order1.refresh_from_db()
        self.assertEqual(order1.status, OrderStatus.COMPLETED)
