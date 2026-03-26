from rest_framework import generics, permissions, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order
from .serializers import OrderSerializer


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


class AllOrdersView(APIView):
    """List all orders with customer and item details for internal dashboard."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.all()
        result = []
        for order in orders:
            result.append({
                "id": order.pk,
                "customer_email": order.user.email,
                "customer_name": order.user.get_full_name(),
                "status": order.status,
                "total": str(order.total),
                "items": [
                    {
                        "product_name": item.product.name,
                        "quantity": item.quantity,
                        "unit_price": str(item.unit_price),
                    }
                    for item in order.items.all()
                ],
                "created_at": order.created_at.isoformat(),
            })
        return Response(result)
