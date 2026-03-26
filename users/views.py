from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import User
from .serializers import UserCreateSerializer, UserSerializer


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# --- Admin Management Endpoints ---


class AdminUserListView(generics.ListAPIView):
    """List all users for admin dashboard."""

    queryset = User.objects.all()
    serializer_class = UserSerializer


class AdminUserDeleteView(generics.DestroyAPIView):
    """Delete a user account."""

    queryset = User.objects.all()
    serializer_class = UserSerializer


@api_view(["POST"])
def admin_reset_password(request, pk):
    """Reset a user's password to a temporary value."""
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    temp_password = "TempPass123!"
    user.set_password(temp_password)
    user.save()
    return Response({
        "message": f"Password reset for {user.username}",
        "temporary_password": temp_password,
    })


@api_view(["GET"])
def user_order_history(request, pk):
    """View any user's order history."""
    from orders.models import Order

    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    orders = Order.objects.filter(user=user).values(
        "id", "status", "total", "created_at"
    )
    return Response({
        "user": user.username,
        "orders": list(orders),
    })
