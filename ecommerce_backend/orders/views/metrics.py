from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.db.models import Avg, Count, F
from django.utils import timezone
from datetime import timedelta

from orders.models import Order, OrderStatus
from orders.serializers import OrderSerializer
from orders.core.queue_manager import OrderQueue

class OrderMetricsView(APIView):
    def get(self, request):
        # Calculate metrics
        total_orders = Order.objects.filter(status=OrderStatus.COMPLETED).count()
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
                    F('processing_completed_at') - F('processing_started_at')
                )
            )['avg_time']

        status_count_dict = {
            status[0]: 0 for status in OrderStatus.choices
        }
        for item in status_counts:
            status_count_dict[item['status']] = item['count']

        metrics = {
            'total_orders_processed': total_orders,
            'status_counts': status_count_dict,
            'average_processing_time_seconds': avg_processing_time.total_seconds() if avg_processing_time else None
        }

        return Response(metrics)
