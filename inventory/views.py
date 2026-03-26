import logging

from django.db.models import Q
from products.models import Product
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import InventoryLog, StockAlert
from .serializers import (
    InventoryLogSerializer,
    ProductSearchSerializer,
    StockAlertSerializer,
    StockUpdateSerializer,
)

logger = logging.getLogger(__name__)


class ProductSearchView(APIView):
    """Search and filter products.

    Issue 2: Builds filters dynamically from user input without validation.
    Issue 4: Returns all fields to unauthenticated users.
    Issue 11: Sorting done in Python instead of database.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        queryset = Product.objects.filter(is_active=True)

        # Text search
        query = request.query_params.get("q", "")
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )

        # Issue 2: Dynamic filter building from user input without allowlist
        # Any field can be filtered, including internal ones like is_active, etc.
        for param, value in request.query_params.items():
            if param in ("q", "sort", "page", "page_size"):
                continue
            try:
                queryset = queryset.filter(**{param: value})
            except Exception:
                # Issue 9: Array values or invalid params crash with 500
                # Should return 400, but we just skip silently
                continue

        # Issue 11: Python-level sorting instead of DB ordering
        sort_by = request.query_params.get("sort", "name")
        results = list(queryset)
        try:
            results.sort(key=lambda p: getattr(p, sort_by, p.name))
        except (AttributeError, TypeError):
            pass

        # Issue 4: All fields exposed to unauthenticated users
        serializer = ProductSearchSerializer(results, many=True)
        return Response(serializer.data)


class StockLevelView(APIView):
    """Get current stock levels for all products."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Issue 6: N+1 — loops over products and checks inventory log per product
        products = Product.objects.filter(is_active=True)
        stock_data = []
        for product in products:
            # Fetches last log entry per product — N+1 query
            last_log = InventoryLog.objects.filter(
                product=product
            ).first()
            stock_data.append({
                "product_id": product.pk,
                "product_name": product.name,
                "current_stock": product.stock,
                "last_change": InventoryLogSerializer(last_log).data if last_log else None,
            })
        return Response(stock_data)


class StockUpdateView(APIView):
    """Update stock level for a product."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = StockUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data["product_id"]
        quantity_change = serializer.validated_data["quantity_change"]

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Issue 1: Read-modify-write without F() or select_for_update()
        # Classic oversell race condition
        previous_stock = product.stock
        new_stock = previous_stock + quantity_change

        if new_stock < 0:
            return Response(
                {"error": "Insufficient stock."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product.stock = new_stock
        product.save()

        # Log the change
        InventoryLog.objects.create(
            product=product,
            change_type=serializer.validated_data["change_type"],
            quantity_change=quantity_change,
            previous_stock=previous_stock,
            new_stock=new_stock,
            notes=serializer.validated_data.get("notes", ""),
            created_by=request.user,
        )

        return Response({
            "product_id": product.pk,
            "previous_stock": previous_stock,
            "new_stock": new_stock,
        })


class InventoryHistoryView(APIView):
    """Get inventory change history for a product.

    Issue 5: No pagination — returns ALL history entries.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, product_id):
        # Issue 5: Returns all logs without pagination — unbounded query
        logs = InventoryLog.objects.filter(product_id=product_id)
        serializer = InventoryLogSerializer(logs, many=True)
        return Response(serializer.data)


class StockAlertListView(APIView):
    """List active stock alerts."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        alerts = StockAlert.objects.filter(
            alert_status=StockAlert.Status.ACTIVE
        ).select_related("product")
        serializer = StockAlertSerializer(alerts, many=True)
        return Response(serializer.data)
