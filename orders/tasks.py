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
