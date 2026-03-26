from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import Product

from .models import Order, OrderItem
from .serializers import OrderCreateSerializer, OrderSerializer


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


class CheckoutView(APIView):
    """Process checkout: validate stock, create order, decrement inventory."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items_data = serializer.validated_data["items"]
        shipping_address = serializer.validated_data["shipping_address"]

        # Validate stock availability
        for item_data in items_data:
            product = Product.objects.get(pk=item_data["product_id"])
            if product.stock < item_data["quantity"]:
                return Response(
                    {"error": f"Insufficient stock for {product.name}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Create the order
        order = Order.objects.create(
            user=request.user,
            shipping_address=shipping_address,
        )

        total = 0
        for item_data in items_data:
            product = Product.objects.get(pk=item_data["product_id"])
            quantity = item_data["quantity"]

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=product.price,
            )

            # Decrement stock
            product.stock -= quantity
            product.save()

            total += product.price * quantity

        order.total = total
        order.save()

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )
