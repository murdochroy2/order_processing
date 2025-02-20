from django.core.management.base import BaseCommand
from django.utils import timezone
from orders.models import Order
import random
import uuid

class Command(BaseCommand):
    help = 'Populates the database with sample orders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of orders to create'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Sample data
        sample_items = [
            {"id": "ITEM001", "name": "Laptop", "price": 999.99},
            {"id": "ITEM002", "name": "Smartphone", "price": 699.99},
            {"id": "ITEM003", "name": "Headphones", "price": 199.99},
            {"id": "ITEM004", "name": "Tablet", "price": 499.99},
            {"id": "ITEM005", "name": "Smartwatch", "price": 299.99},
        ]
        
        sample_user_ids = [f"USER{i:03d}" for i in range(1, 6)]
        
        for _ in range(count):
            # Generate random order data
            num_items = random.randint(1, 3)
            selected_items = random.sample(sample_items, num_items)
            item_ids = [item["id"] for item in selected_items]
            total_amount = sum(item["price"] for item in selected_items)
            
            # Create order
            order = Order.objects.create(
                order_id=f"ORD-{uuid.uuid4().hex[:8].upper()}",
                user_id=random.choice(sample_user_ids),
                item_ids=item_ids,
                total_amount=total_amount,
                status=random.choice(['PENDING', 'PROCESSING', 'COMPLETED'])
            )
            
            # If order is processing or completed, set processing dates
            if order.status in ['PROCESSING', 'COMPLETED']:
                order.processing_started_at = order.created_at + timezone.timedelta(hours=random.randint(1, 24))
                
                if order.status == 'COMPLETED':
                    order.processing_completed_at = order.processing_started_at + timezone.timedelta(seconds=random.randint(1, 60))
                
                order.save()

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {count} sample orders')
        )
