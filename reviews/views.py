from rest_framework import permissions, viewsets

from .models import Review
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Review.objects.select_related("user", "product")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
