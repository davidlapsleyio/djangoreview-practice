import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def send_order_confirmation_email(order_id):
    """Send order confirmation email to customer."""
    from .models import Order

    try:
        order = Order.objects.select_related("user").get(pk=order_id)
    except Order.DoesNotExist:
        logger.error("Order %s not found for confirmation email.", order_id)
        return

    logger.info(
        "Sending confirmation email for order #%s to %s",
        order.pk,
        order.user.email,
    )


@shared_task
def process_order(order_id):
    """Process a confirmed order: charge payment and update status."""
    from .models import Order

    order = Order.objects.get(pk=order_id)

    # Charge the payment (simulated)
    logger.info("Charging payment for order #%s: $%s", order.pk, order.total)

    # Update status to confirmed
    order.status = Order.Status.CONFIRMED
    order.save()

    # Send confirmation
    send_order_confirmation_email(order_id)

    logger.info("Order #%s processed successfully.", order.pk)
    return {"order_id": order.pk, "status": "confirmed"}
