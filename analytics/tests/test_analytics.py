from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from orders.models import Order
from products.models import Category, Product
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class DashboardTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="analyst", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            name="Widget",
            price=Decimal("29.99"),
            stock=100,
            category=self.category,
        )
        for i in range(5):
            Order.objects.create(
                user=self.user,
                total=Decimal("99.99"),
                shipping_address="123 Main St",
                status=Order.Status.CONFIRMED,
            )

    def test_dashboard_returns_metrics(self):
        """Test dashboard returns revenue metrics."""
        response = self.client.get("/api/analytics/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_revenue", response.data)
        self.assertIn("order_count", response.data)
        self.assertIn("average_order_value", response.data)

    def test_dashboard_with_date_range(self):
        """Test dashboard with date filtering."""
        response = self.client.get(
            "/api/analytics/dashboard/?start_date=2024-01-01&end_date=2024-12-31"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CohortTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="analyst", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_cohort_analysis(self):
        """Test cohort analysis returns data."""
        response = self.client.get("/api/analytics/cohort/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("cohorts", response.data)


class ExportTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="analyst", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    @patch("analytics.tasks.generate_report.delay")
    def test_export_creates_report(self, mock_task):
        """Test export creates a report record."""
        data = {
            "report_type": "orders",
            "report_format": "csv",
        }
        response = self.client.post("/api/analytics/export/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # No tests for:
    # - Permission restrictions on dashboard/reports
    # - Path traversal in download
    # - Large dataset handling (OOM)
    # - Report timeout scenarios
    # - Multi-tenant data isolation
