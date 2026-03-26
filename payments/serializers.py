from rest_framework import serializers

from .models import Payment, Refund


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id", "order", "user", "amount", "currency",
            "payment_status", "provider_transaction_id",
            "payment_method", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "user", "payment_status", "provider_transaction_id", "created_at", "updated_at"]


class ChargeSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    # Issue 2: Amount taken from request body instead of calculated server-side
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=3, default="USD")
    payment_method = serializers.CharField(max_length=50, default="card")
    card_number = serializers.CharField(max_length=20)
    card_expiry = serializers.CharField(max_length=5)
    card_cvc = serializers.CharField(max_length=4)


class RefundSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    reason = serializers.CharField(required=False, default="")


class WebhookEventSerializer(serializers.Serializer):
    event_type = serializers.CharField()
    transaction_id = serializers.CharField()
    status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    metadata = serializers.DictField(required=False, default=dict)


class RefundDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ["id", "payment", "amount", "reason", "refund_status", "provider_refund_id", "created_at"]
