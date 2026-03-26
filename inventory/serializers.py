from products.models import Product
from rest_framework import serializers

from .models import InventoryLog, ReorderRequest, StockAlert


class InventoryLogSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = InventoryLog
        fields = [
            "id", "product", "product_name", "change_type",
            "quantity_change", "previous_stock", "new_stock",
            "notes", "created_by", "created_at",
        ]


class StockAlertSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = StockAlert
        fields = [
            "id", "product", "product_name", "threshold",
            "current_stock", "alert_status", "created_at",
        ]


class ProductSearchSerializer(serializers.ModelSerializer):
    """Serializer for search results.

    Issue 4: Exposes cost_price to unauthenticated users.
    """
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        # Issue 4: Returns ALL fields including internal ones
        fields = "__all__"


class StockUpdateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity_change = serializers.IntegerField()
    change_type = serializers.ChoiceField(choices=InventoryLog.ChangeType.choices)
    notes = serializers.CharField(required=False, default="")


class ReorderRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReorderRequest
        fields = ["id", "product", "quantity", "is_processed", "created_at"]
