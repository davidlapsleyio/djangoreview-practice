from decimal import Decimal

import pytest

from orders.models import Order, OrderItem
from products.models import Category, Product
from users.models import User


@pytest.mark.django_db
class TestOrderModel:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(username="buyer", password="testpass123")

    @pytest.fixture
    def category(self):
        return Category.objects.create(name="Gadgets", slug="gadgets")

    @pytest.fixture
    def product(self, category):
        return Product.objects.create(
            name="Gizmo", price=Decimal("29.99"), stock=10, category=category
        )

    @pytest.fixture
    def order(self, user):
        return Order.objects.create(user=user, shipping_address="456 Oak Ave")

    def test_order_str(self, order):
        assert f"Order #{order.pk}" in str(order)

    def test_order_item_line_total(self, order, product):
        item = OrderItem.objects.create(
            order=order, product=product, quantity=3, unit_price=Decimal("29.99")
        )
        assert item.line_total == Decimal("89.97")

    def test_recalculate_total(self, order, product):
        OrderItem.objects.create(
            order=order, product=product, quantity=2, unit_price=Decimal("29.99")
        )
        order.recalculate_total()
        order.refresh_from_db()
        assert order.total == Decimal("59.98")
