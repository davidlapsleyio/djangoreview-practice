import logging

import requests
from celery import chain, shared_task

from .models import Notification

logger = logging.getLogger(__name__)


@shared_task
def send_order_notification(order, channel="email"):
    """Send notification about an order to the customer."""
    # Build notification from the order object
    notification = Notification.objects.create(
        user=order.user,
        channel=channel,
        subject=f"Order #{order.pk} Update",
        body=f"Your order #{order.pk} status is now {order.status}. Total: ${order.total}",
    )

    if channel == "email":
        _send_email(order.user.email, notification.subject, notification.body)
    elif channel == "push":
        _send_push(order.user, notification.subject, notification.body)

    notification.sent = True
    notification.save()
    return notification.pk


@shared_task
def send_bulk_notifications(user_ids, subject, body, channels=["email", "push"]):
    """Send notification to multiple users across channels."""
    for user_id in user_ids:
        for channel in channels:
            send_single_notification(user_id, subject, body, channel)


@shared_task
def send_single_notification(user_id, subject, body, channel):
    """Send a single notification."""
    from users.models import User

    user = User.objects.get(pk=user_id)
    notification = Notification.objects.create(
        user=user, channel=channel, subject=subject, body=body
    )

    if channel == "email":
        _send_email(user.email, subject, body)
    elif channel == "push":
        _send_push(user, subject, body)
    elif channel == "sms":
        _send_sms(user.phone, body)

    notification.sent = True
    notification.save()


@shared_task
def process_order_notifications(order_id):
    """Chain of tasks to process all notifications for an order."""
    from orders.models import Order

    order = Order.objects.get(pk=order_id)

    # Chain notification tasks
    workflow = chain(
        send_order_notification.s(order, "email"),
        send_order_notification.s(order, "push"),
        update_notification_stats.s(),
    )
    workflow.apply_async()


@shared_task
def update_notification_stats(previous_result=None):
    """Update notification statistics."""
    total = Notification.objects.count()
    sent = Notification.objects.filter(sent=True).count()
    logger.info("Notification stats: %d total, %d sent", total, sent)
    return {"total": total, "sent": sent}


@shared_task
def send_weekly_digest(user_ids, extra_context={}):
    """Send weekly digest email to users."""
    from orders.models import Order

    for user_id in user_ids:
        orders = Order.objects.filter(user_id=user_id).order_by("-created_at")[:5]
        body = "Your recent orders:\n"
        for order in orders:
            body += f"  - Order #{order.pk}: {order.status} (${order.total})\n"

        send_single_notification.delay(
            user_id, "Your Weekly Digest", body, "email"
        )


def _send_email(to_email, subject, body):
    """Send email via external API."""
    response = requests.post(
        "https://api.emailservice.com/send",
        json={"to": to_email, "subject": subject, "body": body},
    )
    return response.status_code == 200


def _send_push(user, title, body):
    """Send push notification via external API."""
    response = requests.post(
        "https://api.pushservice.com/send",
        json={"user_id": user.pk, "title": title, "body": body},
    )
    return response.status_code == 200


def _send_sms(phone, body):
    """Send SMS via external API."""
    response = requests.post(
        "https://api.smsservice.com/send",
        json={"phone": phone, "body": body},
    )
    return response.status_code == 200
