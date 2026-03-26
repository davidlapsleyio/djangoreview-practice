from rest_framework import generics, permissions

from .models import User
from .serializers import UserCreateSerializer, UserDetailSerializer, UserSerializer


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
