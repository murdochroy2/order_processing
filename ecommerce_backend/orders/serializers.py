from rest_framework import serializers
from .models import Order, OrderStatus

class OrderSerializer(serializers.Serializer):
    order_id = serializers.CharField(max_length=50)
    user_id = serializers.CharField(max_length=50)
    item_ids = serializers.JSONField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    status = serializers.ChoiceField(choices=OrderStatus.choices, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    processing_started_at = serializers.DateTimeField(read_only=True)
    processing_completed_at = serializers.DateTimeField(read_only=True)

    def validate_total_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Total amount must be greater than zero")
        return value

    def validate_item_ids(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("item_ids must be a list")
        if not value:
            raise serializers.ValidationError("item_ids cannot be empty")
        return value

    def create(self, validated_data):
        return Order.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.order_id = validated_data.get('order_id', instance.order_id)
        instance.user_id = validated_data.get('user_id', instance.user_id)
        instance.item_ids = validated_data.get('item_ids', instance.item_ids)
        instance.total_amount = validated_data.get('total_amount', instance.total_amount)
        instance.save()
        return instance