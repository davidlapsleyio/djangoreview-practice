from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .tasks import send_bulk_notifications


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def send_notification(request):
    """Trigger a notification to specified users."""
    user_ids = request.data.get("user_ids", [])
    subject = request.data.get("subject", "")
    body = request.data.get("body", "")
    channels = request.data.get("channels", ["email"])

    if not user_ids or not subject:
        return Response(
            {"error": "user_ids and subject are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    send_bulk_notifications.delay(user_ids, subject, body, channels)
    return Response({"message": "Notifications queued"})
