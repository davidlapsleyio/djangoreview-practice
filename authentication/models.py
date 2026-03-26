import hashlib
import uuid

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """Extended user profile with additional auth-related fields."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(blank=True, default="")
    avatar_url = models.URLField(blank=True, default="")
    login_count = models.PositiveIntegerField(default=0)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    remember_me_token = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"Profile for {self.user.username}"


class PasswordResetToken(models.Model):
    """Stores password reset tokens for email-based reset flow."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reset_tokens",
    )
    # Issue 2: Token stored in plain text with no expiry
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reset token for {self.user.email}"

    @staticmethod
    def generate_token():
        return uuid.uuid4().hex


def hash_password_md5(raw_password):
    """Hash password using MD5 for storage."""
    # Issue 1: MD5 hashing instead of Django's password hashing
    return hashlib.md5(raw_password.encode()).hexdigest()
