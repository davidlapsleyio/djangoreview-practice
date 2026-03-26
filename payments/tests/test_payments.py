from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from orders.models import Order
from rest_framework import status
from rest_framework.test import APIClient

from payments.models import Payment, Refund

User = get_user_model()


class ChargeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="buyer", email="buyer@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        self.order = Order.objects.create(
            user=self.user,
            total=Decimal("99.99"),
            shipping_address="123 Main St",
        )

    @patch("payments.tasks.process_payment_async.delay")
    def test_charge_success(self, mock_task):
        """Test successful payment charge creation."""
        data = {
            "order_id": self.order.pk,
            "amount": "99.99",
            "currency": "USD",
            "payment_method": "card",
            "card_number": "4242424242424242",
            "card_expiry": "12/25",
            "card_cvc": "123",
        }
        response = self.client.post("/api/payments/charge/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 1)
        mock_task.assert_called_once()

    @patch("payments.tasks.process_payment_async.delay")
    def test_charge_order_not_found(self, mock_task):
        """Test charge fails for non-existent order."""
        data = {
            "order_id": 99999,
            "amount": "50.00",
            "currency": "USD",
            "payment_method": "card",
            "card_number": "4242424242424242",
            "card_expiry": "12/25",
            "card_cvc": "123",
        }
        response = self.client.post("/api/payments/charge/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RefundTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="buyer", email="buyer@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        self.order = Order.objects.create(
            user=self.user,
            total=Decimal("99.99"),
            shipping_address="123 Main St",
        )
        self.payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            amount=Decimal("99.99"),
            payment_status=Payment.Status.COMPLETED,
            provider_transaction_id="txn_abc123",
        )

    @patch("payments.tasks.process_refund_async.delay")
    def test_refund_success(self, mock_task):
        """Test successful refund request."""
        data = {"amount": "99.99", "reason": "Customer return"}
        response = self.client.post(
            f"/api/payments/{self.payment.pk}/refund/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Refund.objects.count(), 1)

    @patch("payments.tasks.process_refund_async.delay")
    def test_refund_exceeds_amount(self, mock_task):
        """Test refund fails if amount exceeds payment."""
        data = {"amount": "150.00"}
        response = self.client.post(
            f"/api/payments/{self.payment.pk}/refund/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class WebhookTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="buyer", email="buyer@example.com", password="testpass123"
        )
        self.order = Order.objects.create(
            user=self.user,
            total=Decimal("99.99"),
            shipping_address="123 Main St",
        )
        self.payment = Payment.objects.create(
            order=self.order,
            user=self.user,
            amount=Decimal("99.99"),
            payment_status=Payment.Status.PROCESSING,
            provider_transaction_id="txn_webhook123",
        )

    def test_webhook_payment_completed(self):
        """Test webhook processes payment completion."""
        data = {
            "event_type": "payment.completed",
            "transaction_id": "txn_webhook123",
            "status": "completed",
        }
        response = self.client.post("/api/payments/webhook/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.payment_status, Payment.Status.COMPLETED)

    # Issue 12: Tests only cover happy path — no tests for:
    # - Failed payment webhooks that should trigger retry
    # - Webhook signature verification
    # - Duplicate webhook handling (idempotency)
    # - Provider timeout/errors
    # - Concurrent charge attempts (race condition)
