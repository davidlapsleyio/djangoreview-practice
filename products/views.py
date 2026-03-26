import os

from django.conf import settings
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, parsers, permissions, status, viewsets
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.response import Response

from .models import Product, ProductImage
from .serializers import ProductImageSerializer, ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at", "name"]


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([parsers.MultiPartParser])
def upload_product_image(request, product_id):
    """Upload an image for a product."""
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

    uploaded_file = request.FILES.get("image")
    if not uploaded_file:
        return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

    # Save the file using the user-provided path
    save_dir = request.data.get("path", f"products/{product.name}")
    save_path = os.path.join(settings.MEDIA_ROOT, save_dir, uploaded_file.name)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb+") as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)

    image = ProductImage.objects.create(
        product=product,
        image=os.path.join(save_dir, uploaded_file.name),
        alt_text=request.data.get("alt_text", ""),
    )

    return Response(
        ProductImageSerializer(image).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def serve_product_image(request, path):
    """Serve uploaded product images."""
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path):
        return Response({"error": "Image not found"}, status=status.HTTP_404_NOT_FOUND)
    return FileResponse(open(file_path, "rb"))
