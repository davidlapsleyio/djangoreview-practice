import json

from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem
from products.models import Category, Product
from rest_framework import serializers
from reviews.models import Review

User = get_user_model()


class DynamicFieldsSerializer(serializers.ModelSerializer):
    """A serializer that takes an optional `fields` argument to
    dynamically limit the fields returned.

    Issue 1: Allows selecting ANY model attribute, including internal ones.
    Issue 2: Expansion can expose sensitive nested fields.
    """

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)
        expand = kwargs.pop("expand", None)
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Issue 1: No allowlist — any field can be requested
            allowed = set(fields.split(","))
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        if expand is not None:
            # Issue 2: Expand allows accessing any related field
            for relation in expand.split(","):
                parts = relation.strip().split(".")
                if len(parts) >= 1:
                    rel_name = parts[0]
                    try:
                        model = self.Meta.model
                        rel_field = model._meta.get_field(rel_name)
                        if rel_field.is_relation:
                            related_model = rel_field.related_model
                            # Dynamically create a nested serializer
                            nested_serializer = type(
                                f"{related_model.__name__}ExpandSerializer",
                                (serializers.ModelSerializer,),
                                {
                                    "Meta": type(
                                        "Meta", (), {"model": related_model, "fields": "__all__"}
                                    )
                                },
                            )
                            self.fields[rel_name] = nested_serializer(read_only=True)
                    except Exception:
                        pass


class ProductV2Serializer(DynamicFieldsSerializer):
    class Meta:
        model = Product
        fields = [
            "id", "name", "description", "price", "stock",
            "category", "is_active", "created_at", "updated_at",
        ]


class OrderV2Serializer(DynamicFieldsSerializer):
    class Meta:
        model = Order
        fields = [
            "id", "user", "status", "total", "shipping_address",
            "created_at", "updated_at",
        ]


class UserV2Serializer(DynamicFieldsSerializer):
    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "is_active", "date_joined",
        ]


class BulkCreateProductSerializer(serializers.Serializer):
    """Serializer for bulk product creation.

    Issue 11: No schema validation on individual items.
    """
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
    )


class BulkDeleteSerializer(serializers.Serializer):
    """Serializer for bulk deletion."""
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
    )


class BulkUpdateSerializer(serializers.Serializer):
    """Serializer for bulk updates."""
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
    )
