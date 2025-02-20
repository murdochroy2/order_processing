import queue
import threading
import time
from datetime import datetime
from django.db import IntegrityError, connection
from django.utils import timezone
from .models import Order, OrderStatus

class OrderQueue:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(OrderQueue, cls).__new__(cls)
                cls._instance.queue = queue.Queue()
                cls._instance.processing_thread = None
                cls._instance.is_running = False
            return cls._instance

    def start_processing(self):
        if not self.is_running:
            self.is_running = True
            self.processing_thread = threading.Thread(target=self._process_orders)
            self.processing_thread.daemon = True
            self.processing_thread.start()

    def add_order(self, order):
        self.queue.put(order)

    def _process_orders(self):
        while self.is_running:
            try:
                order = self.queue.get(timeout=1)
                order.status = OrderStatus.PROCESSING
                order.processing_started_at = timezone.now()
                order.save()

                order.status = OrderStatus.COMPLETED
                order.processing_completed_at = timezone.now()
                order.save()
                self.queue.task_done()
            except queue.Empty:
                continue
            except IntegrityError as e:
                if 'unique constraint' in str(e).lower():
                    print(f"Duplicate order detected: {e}")
                    self.queue.task_done()
                else:
                    print(f"Database integrity error: {e}")
            except Exception as e:
                print(f"Error processing order: {e}")
            finally:
                # Close the database connection after each iteration
                connection.close()

    def stop_processing(self):
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join()