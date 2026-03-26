from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        PUSH = "push", "Push Notification"
        SMS = "sms", "SMS"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    channel = models.CharField(max_length=10, choices=Channel.choices)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.channel}: {self.subject} -> {self.user.username}"
