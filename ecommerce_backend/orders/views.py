from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.db.models import Avg, Count, F
from django.utils import timezone
from datetime import timedelta

from .models import Order, OrderStatus
from .serializers import OrderSerializer
from .queue_manager import OrderQueue

# Create your views here.

class OrderView(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue_manager = OrderQueue()
        self.queue_manager.start_processing()

    def get(self, request, order_id=None):
        if order_id:
            order = get_object_or_404(Order, order_id=order_id)
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        
        orders = Order.objects.all()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        self.queue_manager.add_order(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
