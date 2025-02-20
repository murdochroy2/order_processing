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