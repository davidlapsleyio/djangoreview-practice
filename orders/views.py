from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, OrderItem
from .serializers import (
    OrderItemUpdateSerializer,
    OrderSerializer,
    OrderUpdateSerializer,
)


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .select_related("user")
            .prefetch_related("items", "items__product", "items__product__category")
        )


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .select_related("user")
            .prefetch_related("items", "items__product", "items__product__category")
        )


class OrderUpdateView(generics.UpdateAPIView):
    """Update any field on an order."""

    queryset = Order.objects.all()
    serializer_class = OrderUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]


class OrderItemCreateView(APIView):
    """Add an item to any order."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_pk):
        serializer = OrderItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BulkOrderUpdateView(APIView):
    """Bulk update order statuses."""

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        updates = request.data.get("orders", [])
        updated = []
        for update_data in updates:
            order_id = update_data.get("id")
            try:
                order = Order.objects.get(pk=order_id)
            except Order.DoesNotExist:
                continue
            serializer = OrderUpdateSerializer(order, data=update_data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            updated.append(order_id)
        return Response({"updated": updated})
