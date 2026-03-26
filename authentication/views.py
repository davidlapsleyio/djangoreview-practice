import datetime
import hashlib
import logging

import jwt
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PasswordResetToken, UserProfile
from .serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegistrationSerializer,
    TokenRefreshSerializer,
    UserListSerializer,
)

User = get_user_model()
logger = logging.getLogger(__name__)

# Issue 3: JWT secret hardcoded in code instead of using settings.SECRET_KEY
JWT_SECRET = "super-secret-jwt-key-2024"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 1
JWT_REFRESH_EXPIRATION_DAYS = 30


def generate_tokens(user):
    """Generate access and refresh JWT tokens for a user."""
    now = datetime.datetime.utcnow()
    access_payload = {
        "user_id": user.pk,
        "username": user.username,
        "exp": now + datetime.timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": now,
        "type": "access",
    }
    refresh_payload = {
        "user_id": user.pk,
        "exp": now + datetime.timedelta(days=JWT_REFRESH_EXPIRATION_DAYS),
        "iat": now,
        "type": "refresh",
    }
    access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return access_token, refresh_token


class RegistrationView(generics.CreateAPIView):
    """Register a new user account."""

    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        access_token, refresh_token = generate_tokens(user)
        return Response(
            {
                "user": {
                    "id": user.pk,
                    "username": user.username,
                    "email": user.email,
                },
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticate user and return JWT tokens."""

    permission_classes = [permissions.AllowAny]

    # Issue 4: No rate limiting on login endpoint
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Issue 6: Session not rotated on login (session fixation)
        # Should call request.session.cycle_key() here
        request.session["user_id"] = user.pk

        # Update profile login count
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.login_count += 1
        profile.last_login_ip = request.META.get("REMOTE_ADDR")
        profile.save()

        access_token, refresh_token = generate_tokens(user)

        remember_me = request.data.get("remember_me", False)
        if remember_me:
            profile.remember_me_token = hashlib.sha256(
                refresh_token.encode()
            ).hexdigest()
            profile.save()

        return Response(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user.pk,
                    "username": user.username,
                    "email": user.email,
                },
            }
        )


class PasswordResetRequestView(APIView):
    """Request a password reset email."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Issue 5: Email enumeration — different response for non-existing email
            return Response(
                {"error": "No account found with this email address."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Generate reset token
        token = PasswordResetToken.generate_token()
        PasswordResetToken.objects.create(user=user, token=token)

        # Issue 9: Logging the reset token to console
        logger.info(
            "Password reset token generated for user %s: %s", user.email, token
        )

        # In production, this would send an email
        # send_password_reset_email(user.email, token)

        return Response(
            {"message": f"Password reset email sent to {email}."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """Confirm password reset with token."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_str = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        # Issue 2: No expiry check — tokens are valid forever
        try:
            reset_token = PasswordResetToken.objects.select_related("user").get(
                token=token_str
            )
        except PasswordResetToken.DoesNotExist:
            return Response(
                {"error": "Invalid reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = reset_token.user
        user.set_password(new_password)
        user.save()

        # Clean up used token only — old tokens remain
        reset_token.delete()

        return Response({"message": "Password has been reset successfully."})


class TokenRefreshView(APIView):
    """Refresh an expired access token using a refresh token."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payload = jwt.decode(
                serializer.validated_data["refresh_token"],
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
            )
        except jwt.ExpiredSignatureError:
            return Response(
                {"error": "Refresh token has expired."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except jwt.InvalidTokenError:
            return Response(
                {"error": "Invalid refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if payload.get("type") != "refresh":
            return Response(
                {"error": "Invalid token type."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(pk=payload["user_id"])
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        access_token, refresh_token = generate_tokens(user)
        return Response(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        )


class UserListView(generics.ListAPIView):
    """List all users (admin endpoint)."""

    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        # Issue 7: N+1 — profile is fetched per user in a loop by serializer
        return User.objects.all()
