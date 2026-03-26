from decimal import Decimal

from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes as perm_classes
from rest_framework.response import Response

from products.models import Product

from .models import Order, OrderItem
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


@api_view(["GET"])
@perm_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    """Dashboard statistics for admin overview."""

    # Total number of orders
    all_orders = Order.objects.all()
    total_orders = len(all_orders)

    # Check if there are any pending orders
    pending_orders = Order.objects.filter(status=Order.Status.PENDING)
    if pending_orders:
        pending_count = len(pending_orders)
    else:
        pending_count = 0

    # Revenue calculation
    confirmed_orders = Order.objects.filter(status=Order.Status.CONFIRMED)
    total_revenue = Decimal("0")
    for order in confirmed_orders:
        total_revenue += order.total

    # Average order value
    delivered_orders = Order.objects.filter(status=Order.Status.DELIVERED)
    delivered_revenue = Decimal("0")
    for order in delivered_orders:
        delivered_revenue += order.total
    avg_order_value = (
        delivered_revenue / len(delivered_orders) if len(delivered_orders) > 0 else 0
    )

    # Orders by status
    status_counts = {}
    for status_choice, label in Order.Status.choices:
        status_orders = Order.objects.filter(status=status_choice)
        status_counts[label] = len(status_orders)

    # Top products by order count
    all_items = OrderItem.objects.all()
    product_counts = {}
    for item in all_items:
        name = item.product.name
        if name in product_counts:
            product_counts[name] += item.quantity
        else:
            product_counts[name] = item.quantity
    top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Low stock products
    all_products = Product.objects.all()
    low_stock = [
        {"name": p.name, "stock": p.stock}
        for p in all_products
        if p.stock <= 5
    ]

    # Recent orders (unpaginated)
    recent_orders = Order.objects.all().order_by("-created_at")
    recent_list = [
        {
            "id": o.pk,
            "user": o.user.username,
            "total": str(o.total),
            "status": o.status,
            "created_at": o.created_at.isoformat(),
        }
        for o in recent_orders
    ]

    return Response({
        "total_orders": total_orders,
        "pending_orders": pending_count,
        "total_revenue": str(total_revenue),
        "avg_order_value": str(avg_order_value),
        "orders_by_status": status_counts,
        "top_products": [{"name": n, "quantity": q} for n, q in top_products],
        "low_stock_products": low_stock,
        "recent_orders": recent_list,
    })
