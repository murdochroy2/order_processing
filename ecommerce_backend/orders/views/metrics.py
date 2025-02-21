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
        metrics = {
            'total_orders_processed': self._get_total_processed_orders().count(),
            'status_counts': self._get_status_counts(),
            'average_processing_time_seconds': self._get_average_processing_time()
        }
        return Response(metrics)

    def _get_total_processed_orders(self):
        completed_orders = Order.objects.filter(
            status=OrderStatus.COMPLETED,
            processing_started_at__isnull=False,
            processing_completed_at__isnull=False
        )
        
        return completed_orders

    def _get_status_counts(self):
        status_count_dict = {status[0]: 0 for status in OrderStatus.choices}
        # Remove select_for_update() to avoid the error
        status_counts = Order.objects.values('status').annotate(count=Count('status'))
        
        for item in status_counts:
            status_count_dict[item['status']] = item['count']
        
        return status_count_dict

    def _get_average_processing_time(self):
        completed_orders = self._get_total_processed_orders()       
         
        if not completed_orders.exists():
            return None

        avg_processing_time = completed_orders.aggregate(
            avg_time=Avg(F('processing_completed_at') - F('processing_started_at'))
        )['avg_time']
        
        return avg_processing_time.total_seconds() if avg_processing_time else None
