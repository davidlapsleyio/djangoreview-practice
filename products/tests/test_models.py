from decimal import Decimal

import pytest

from products.models import Category, Product


@pytest.mark.django_db
class TestProductModel:
    @pytest.fixture
    def category(self):
        return Category.objects.create(name="Electronics", slug="electronics")

    def test_create_product(self, category):
        product = Product.objects.create(
            name="Widget",
            price=Decimal("19.99"),
            stock=50,
            category=category,
        )
        assert product.name == "Widget"
        assert product.price == Decimal("19.99")
        assert product.stock == 50

    def test_product_str(self, category):
        product = Product(name="Widget", category=category)
        assert str(product) == "Widget"

    def test_category_str(self):
        category = Category(name="Books")
        assert str(category) == "Books"
