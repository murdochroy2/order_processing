from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta

from .models import Order, OrderStatus
from .serializers import OrderSerializer
from .queue_manager import OrderQueue

# Create your views here.

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    lookup_field = 'order_id'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue_manager = OrderQueue()
        self.queue_manager.start_processing()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        self.queue_manager.add_order(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def metrics(self, request):
        # Calculate metrics
        total_orders = Order.objects.count()
        status_counts = Order.objects.values('status').annotate(count=Count('status'))
        
        # Calculate average processing time for completed orders
        completed_orders = Order.objects.filter(
            status=OrderStatus.COMPLETED,
            processing_started_at__isnull=False,
            processing_completed_at__isnull=False
        )
        
        avg_processing_time = None
        if completed_orders.exists():
            avg_processing_time = completed_orders.aggregate(
                avg_time=Avg(
                    'processing_completed_at' - 'processing_started_at'
                )
            )['avg_time']

        status_count_dict = {
            status: 0 for status in OrderStatus.choices
        }
        for item in status_counts:
            status_count_dict[item['status']] = item['count']

        metrics = {
            'total_orders': total_orders,
            'status_counts': status_count_dict,
            'average_processing_time_seconds': avg_processing_time.total_seconds() if avg_processing_time else None
        }

        return Response(metrics)
