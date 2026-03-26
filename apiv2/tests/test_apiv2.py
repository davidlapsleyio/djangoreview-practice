from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from products.models import Category, Product
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class FieldSelectionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            name="Widget",
            description="A widget",
            price=Decimal("29.99"),
            stock=100,
            category=self.category,
        )

    def test_field_selection(self):
        """Test requesting specific fields."""
        response = self.client.get("/api/v2/products/?fields=id,name,price")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data["results"][0]
        self.assertIn("name", result)
        self.assertIn("price", result)

    def test_list_products(self):
        """Test basic product listing."""
        response = self.client.get("/api/v2/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)


class BulkOperationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name="Electronics", slug="electronics")

    def test_bulk_create(self):
        """Test bulk creating products."""
        data = {
            "items": [
                {
                    "name": "Product A",
                    "price": "19.99",
                    "stock": 50,
                    "category_id": self.category.pk,
                },
                {
                    "name": "Product B",
                    "price": "29.99",
                    "stock": 30,
                    "category_id": self.category.pk,
                },
            ]
        }
        response = self.client.post("/api/v2/products/bulk-create/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total_created"], 2)

    def test_bulk_delete(self):
        """Test bulk deleting products."""
        p1 = Product.objects.create(
            name="Delete Me 1", price=Decimal("10.00"), stock=1, category=self.category
        )
        p2 = Product.objects.create(
            name="Delete Me 2", price=Decimal("20.00"), stock=1, category=self.category
        )
        data = {"ids": [p1.pk, p2.pk]}
        response = self.client.delete("/api/v2/products/bulk-delete/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["deleted"], 2)

    # Missing tests for:
    # - Ownership check on bulk delete
    # - Transaction behavior on partial bulk create failure
    # - Size limits on bulk operations
    # - Field selection security (accessing internal fields)
    # - Expand security (nested sensitive data)
    # - Pagination off-by-one
    # - eval() in role-based fields
