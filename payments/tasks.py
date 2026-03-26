import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def process_payment_async(order_id, payment_id, card_details):
    """Process payment asynchronously via Celery.

    Issue 3: Card number logged in plaintext
    Issue 6: Entire objects not passed, but card_details dict contains sensitive data
    """
    from orders.models import Order

    from .models import Payment
    from .provider import PaymentProvider

    # Issue 3: Logging card details including card number in plaintext
    logger.info(
        "Processing payment for order #%s, payment #%s, card: %s",
        order_id, payment_id, card_details,
    )

    try:
        payment = Payment.objects.get(pk=payment_id)
        # Issue 6: Fetching order separately — if we had passed Order object
        # it would be stale. Here we at least fetch fresh, but see views.py
        # for where the order object is passed to task
        order = Order.objects.get(pk=order_id)

        provider = PaymentProvider()
        result = provider.charge(
            amount=payment.amount,
            currency=payment.currency,
            payment_method=payment.payment_method,
            card_details=card_details,
        )

        payment.provider_transaction_id = result["transaction_id"]
        payment.payment_status = Payment.Status.COMPLETED
        payment.save()

        # Issue 9: Raw SQL with f-string interpolation for status update
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE orders_order SET status = 'confirmed' WHERE id = {order.pk}"
            )

        logger.info("Payment #%s completed successfully", payment_id)

    except Exception:
        # Issue 8: Silently swallowing all exceptions
        pass


@shared_task
def process_refund_async(payment_id, refund_id):
    """Process refund asynchronously."""
    from .models import Payment, Refund
    from .provider import PaymentProvider

    try:
        payment = Payment.objects.get(pk=payment_id)
        refund = Refund.objects.get(pk=refund_id)

        provider = PaymentProvider()
        result = provider.refund(
            transaction_id=payment.provider_transaction_id,
            amount=refund.amount,
        )

        refund.provider_refund_id = result["refund_id"]
        refund.refund_status = Refund.Status.COMPLETED
        refund.save()

        payment.payment_status = Payment.Status.REFUNDED
        payment.save()

    except Exception:
        # Issue 8 again: silent exception swallowing
        pass
