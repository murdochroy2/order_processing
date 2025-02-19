from django.db import models
from django.utils import timezone

class OrderStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    COMPLETED = 'COMPLETED', 'Completed'

class Order(models.Model):
    order_id = models.CharField(max_length=50, unique=True)
    user_id = models.CharField(max_length=50)
    item_ids = models.JSONField()  # Store as JSON array
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['user_id']),
            models.Index(fields=['created_at'])
        ]
