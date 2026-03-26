from rest_framework import serializers

from products.serializers import ProductSerializer

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    line_total = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_id", "quantity", "unit_price", "line_total"]
        read_only_fields = ["id", "unit_price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "user", "status", "total", "shipping_address",
            "items", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "user", "total", "created_at", "updated_at"]


class OrderCreateSerializer(serializers.Serializer):
    shipping_address = serializers.CharField()
    items = serializers.ListField(
        child=serializers.DictField(), min_length=1
    )

    def validate_items(self, value):
        for item in value:
            if "product_id" not in item or "quantity" not in item:
                raise serializers.ValidationError(
                    "Each item must have product_id and quantity."
                )
            if item["quantity"] < 1:
                raise serializers.ValidationError("Quantity must be at least 1.")
        return value
