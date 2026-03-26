import logging

from django.db import connection
from orders.models import Order
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment, Refund
from .serializers import (
    ChargeSerializer,
    PaymentSerializer,
    RefundDetailSerializer,
    RefundSerializer,
    WebhookEventSerializer,
)
from .tasks import process_payment_async

logger = logging.getLogger(__name__)


class ChargeView(APIView):
    """Create a new payment charge for an order."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChargeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data["order_id"]
        try:
            order = Order.objects.get(pk=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Issue 2: Using amount from request instead of order.total
        amount = serializer.validated_data["amount"]

        # Issue 7: DB record created before payment is confirmed
        # Payment saved with PENDING, but if Celery task fails silently (Issue 8),
        # we have a payment record with no actual charge
        payment = Payment.objects.create(
            order=order,
            user=request.user,
            amount=amount,
            currency=serializer.validated_data["currency"],
            payment_method=serializer.validated_data["payment_method"],
            payment_status=Payment.Status.PROCESSING,
        )

        # Issue 4: No idempotency key — double-click sends two charges
        # Issue 6: Passing card_details dict (with sensitive data) to Celery task
        card_details = {
            "card_number": serializer.validated_data["card_number"],
            "card_expiry": serializer.validated_data["card_expiry"],
            "card_cvc": serializer.validated_data["card_cvc"],
        }
        process_payment_async.delay(order.pk, payment.pk, card_details)

        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )


class PaymentDetailView(APIView):
    """Get payment details."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, payment_id):
        try:
            payment = Payment.objects.get(pk=payment_id, user=request.user)
        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(PaymentSerializer(payment).data)


class RefundView(APIView):
    """Request a refund for a payment."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, payment_id):
        # Issue 5: No authorization check — any authenticated user can refund any order
        try:
            payment = Payment.objects.get(pk=payment_id)
        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refund_amount = serializer.validated_data.get("amount", payment.amount)
        if refund_amount > payment.amount:
            return Response(
                {"error": "Refund amount exceeds payment amount."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refund = Refund.objects.create(
            payment=payment,
            amount=refund_amount,
            reason=serializer.validated_data.get("reason", ""),
        )

        from .tasks import process_refund_async
        process_refund_async.delay(payment.pk, refund.pk)

        return Response(
            RefundDetailSerializer(refund).data,
            status=status.HTTP_201_CREATED,
        )


class WebhookView(APIView):
    """Handle payment provider webhook callbacks.

    Issue 1: No signature verification — anyone can fake payment events.
    Issue 11: No idempotency — replaying a webhook double-processes.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Issue 1: Webhook signature is never verified
        serializer = WebhookEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event_type = serializer.validated_data["event_type"]
        transaction_id = serializer.validated_data["transaction_id"]
        event_status = serializer.validated_data["status"]

        logger.info(
            "Webhook received: type=%s, txn=%s, status=%s",
            event_type, transaction_id, event_status,
        )

        # Issue 11: No idempotency check — if webhook is replayed, we process again
        if event_type == "payment.completed":
            try:
                payment = Payment.objects.get(
                    provider_transaction_id=transaction_id
                )
                payment.payment_status = Payment.Status.COMPLETED
                payment.save()

                # Update order status via raw SQL
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"UPDATE orders_order SET status = 'confirmed' "
                        f"WHERE id = {payment.order_id}"
                    )
            except Payment.DoesNotExist:
                logger.warning("Payment not found for transaction: %s", transaction_id)

        elif event_type == "payment.failed":
            try:
                payment = Payment.objects.get(
                    provider_transaction_id=transaction_id
                )
                payment.payment_status = Payment.Status.FAILED
                payment.save()
            except Payment.DoesNotExist:
                logger.warning("Payment not found for transaction: %s", transaction_id)

        elif event_type == "refund.completed":
            try:
                payment = Payment.objects.get(
                    provider_transaction_id=transaction_id
                )
                payment.payment_status = Payment.Status.REFUNDED
                payment.save()
            except Payment.DoesNotExist:
                logger.warning("Payment not found for transaction: %s", transaction_id)

        return Response({"status": "received"})
