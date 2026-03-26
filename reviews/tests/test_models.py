from decimal import Decimal

import pytest

from products.models import Category, Product
from reviews.models import Review
from users.models import User


@pytest.mark.django_db
class TestReviewModel:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(username="reviewer", password="testpass123")

    @pytest.fixture
    def product(self):
        category = Category.objects.create(name="Books", slug="books")
        return Product.objects.create(
            name="Django Book", price=Decimal("39.99"), stock=20, category=category
        )

    def test_create_review(self, user, product):
        review = Review.objects.create(
            product=product, user=user, rating=4, comment="Great book!"
        )
        assert review.rating == 4
        assert review.comment == "Great book!"

    def test_review_str(self, user, product):
        review = Review(product=product, user=user, rating=5)
        assert "reviewer" in str(review)
        assert "5/5" in str(review)

    def test_unique_user_product_review(self, user, product):
        Review.objects.create(product=product, user=user, rating=4)
        with pytest.raises(Exception):
            Review.objects.create(product=product, user=user, rating=3)
