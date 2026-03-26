from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from products.models import Category, Product
from rest_framework import status
from rest_framework.test import APIClient

from inventory.models import InventoryLog, StockAlert

User = get_user_model()


class ProductSearchTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            name="Widget Pro",
            description="A professional widget",
            price=Decimal("29.99"),
            stock=100,
            category=self.category,
        )

    def test_search_by_name(self):
        """Test searching products by name."""
        response = self.client.get("/api/inventory/search/?q=Widget")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Widget Pro")

    def test_search_empty_query(self):
        """Test search with no query returns all active products."""
        response = self.client.get("/api/inventory/search/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)


class StockUpdateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="stockmanager", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            name="Widget",
            price=Decimal("19.99"),
            stock=50,
            category=self.category,
        )

    def test_stock_increase(self):
        """Test increasing stock."""
        data = {
            "product_id": self.product.pk,
            "quantity_change": 20,
            "change_type": "restock",
        }
        response = self.client.post("/api/inventory/stock/update/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 70)

    def test_stock_decrease(self):
        """Test decreasing stock."""
        data = {
            "product_id": self.product.pk,
            "quantity_change": -10,
            "change_type": "sale",
        }
        response = self.client.post("/api/inventory/stock/update/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 40)

    def test_stock_insufficient(self):
        """Test that stock can't go negative."""
        data = {
            "product_id": self.product.pk,
            "quantity_change": -100,
            "change_type": "sale",
        }
        response = self.client.post("/api/inventory/stock/update/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class StockAlertTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="admin", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_alerts(self):
        """Test listing active stock alerts."""
        response = self.client.get("/api/inventory/alerts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
