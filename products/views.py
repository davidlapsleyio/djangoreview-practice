from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at", "name"]


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def product_listing(request):
    """Public product listing with review counts and average ratings."""
    products = Product.objects.filter(is_active=True)
    result = []
    for product in products:
        result.append({
            "id": product.pk,
            "name": product.name,
            "price": str(product.price),
            "category": product.category.name,
            "review_count": product.reviews.count(),
            "avg_rating": _avg_rating(product),
            "in_stock": product.stock > 0,
        })
    return Response(result)


def _avg_rating(product):
    reviews = product.reviews.all()
    if not reviews:
        return None
    return sum(r.rating for r in reviews) / len(reviews)
