import logging

from django.db import connection
from orders.models import Order, OrderItem
from products.models import Category, Product
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import build_filter_from_params, get_role_fields
from .pagination import CursorPagination
from .serializers import (
    BulkCreateProductSerializer,
    BulkDeleteSerializer,
    BulkUpdateSerializer,
    OrderV2Serializer,
    ProductV2Serializer,
)

logger = logging.getLogger(__name__)


class ProductListV2View(APIView):
    """v2 product listing with field selection, expansion, and filtering."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        queryset = Product.objects.filter(is_active=True)

        # Apply flexible filtering
        filter_param = request.query_params.get("filter")
        queryset = build_filter_from_params(queryset, filter_param)

        # Pagination
        paginator = CursorPagination()
        page = paginator.paginate_queryset(queryset, request)

        # Issue 6: N+1 — each expanded relation fetched per object
        fields = request.query_params.get("fields")
        expand = request.query_params.get("expand")
        serializer = ProductV2Serializer(
            page, many=True, fields=fields, expand=expand
        )

        return paginator.get_paginated_response(serializer.data)


class ProductDetailV2View(APIView):
    """v2 product detail with field selection and expansion."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        fields = request.query_params.get("fields")
        expand = request.query_params.get("expand")
        serializer = ProductV2Serializer(
            product, fields=fields, expand=expand
        )
        return Response(serializer.data)


class BulkCreateView(APIView):
    """Bulk create products.

    Issue 4: No transaction wrapping — partial failures leave DB inconsistent.
    Issue 7: No size cap on bulk operations.
    Issue 11: No schema validation on individual items.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = BulkCreateProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data["items"]
        # Issue 7: No size limit — could be 10,000 items
        created = []
        errors = []

        # Issue 4: No transaction — partial creates on failure
        for i, item_data in enumerate(items):
            try:
                # Issue 11: No validation of individual item schema
                product = Product.objects.create(**item_data)
                created.append({"index": i, "id": product.pk, "name": product.name})
            except Exception as e:
                errors.append({"index": i, "error": str(e)})

        return Response({
            "created": created,
            "errors": errors,
            "total_created": len(created),
            "total_errors": len(errors),
        }, status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST)


class BulkDeleteView(APIView):
    """Bulk delete products.

    Issue 3: No ownership check — accepts list of IDs and deletes all.
    Issue 7: No size cap.
    """

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        serializer = BulkDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ids = serializer.validated_data["ids"]
        # Issue 3: No ownership/permission check — deletes any products
        # Issue 7: No limit on number of IDs
        deleted_count, _ = Product.objects.filter(pk__in=ids).delete()

        return Response({
            "deleted": deleted_count,
            "requested": len(ids),
        })


class BulkUpdateView(APIView):
    """Bulk update products."""

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        serializer = BulkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data["items"]
        updated = []
        errors = []

        for i, item_data in enumerate(items):
            try:
                product_id = item_data.pop("id", None)
                if not product_id:
                    errors.append({"index": i, "error": "Missing 'id' field"})
                    continue
                Product.objects.filter(pk=product_id).update(**item_data)
                updated.append({"index": i, "id": product_id})
            except Exception as e:
                errors.append({"index": i, "error": str(e)})

        return Response({
            "updated": updated,
            "errors": errors,
        })


class OrderListV2View(APIView):
    """v2 order listing."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = Order.objects.filter(user=request.user)

        filter_param = request.query_params.get("filter")
        queryset = build_filter_from_params(queryset, filter_param)

        # Apply role-based field filtering
        role_fields = get_role_fields(request.user, "order")

        paginator = CursorPagination()
        page = paginator.paginate_queryset(queryset, request)

        fields = request.query_params.get("fields")
        expand = request.query_params.get("expand")
        serializer = OrderV2Serializer(
            page, many=True, fields=fields, expand=expand
        )

        return paginator.get_paginated_response(serializer.data)
