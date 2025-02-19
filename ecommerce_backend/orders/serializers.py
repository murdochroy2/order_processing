from rest_framework import serializers
from .models import Order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['order_id', 'user_id', 'item_ids', 'total_amount', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']