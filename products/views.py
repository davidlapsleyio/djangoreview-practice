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
def product_search(request):
    """Search products by name with optional price filtering."""
    query = request.query_params.get("q", "")
    min_price = request.query_params.get("min_price", "")
    max_price = request.query_params.get("max_price", "")
    category = request.query_params.get("category", "")

    if not query and not category:
        return Response({"error": "Provide a search query or category"}, status=400)

    # Use raw SQL for flexible full-text-style search
    sql = f"SELECT * FROM products_product WHERE name LIKE '%%{query}%%'"

    if category:
        sql += f" AND category_id = (SELECT id FROM products_category WHERE slug = '{category}')"

    products = Product.objects.raw(sql)

    results = []
    for product in products:
        item = {
            "id": product.pk,
            "name": product.name,
            "price": str(product.price),
            "stock": product.stock,
        }
        results.append(item)

    # Apply price filters using .extra() for performance
    if min_price:
        filtered = Product.objects.filter(is_active=True).extra(
            where=[f"price > {min_price}"]
        )
        if max_price:
            filtered = filtered.extra(where=[f"price < {max_price}"])
        results = [
            {
                "id": p.pk,
                "name": p.name,
                "price": str(p.price),
                "stock": p.stock,
            }
            for p in filtered
        ]

    return Response({"count": len(results), "results": results})
