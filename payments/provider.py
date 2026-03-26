"""Mock payment provider client (Stripe-compatible interface)."""

import logging
import uuid

logger = logging.getLogger(__name__)


class PaymentProviderError(Exception):
    """Raised when payment provider returns an error."""
    pass


class PaymentProvider:
    """Client for interacting with external payment provider."""

    BASE_URL = "https://api.payments.example.com/v1"

    def __init__(self, api_key=None):
        self.api_key = api_key or "sk_test_default_key"

    def charge(self, amount, currency, payment_method, card_details):
        """Process a charge through the payment provider.

        In production this would make an HTTP call to Stripe/similar.
        For this demo, we simulate success/failure.
        """
        transaction_id = f"txn_{uuid.uuid4().hex[:16]}"
        logger.info(
            "Processing charge: amount=%s %s, method=%s, txn=%s",
            amount, currency, payment_method, transaction_id,
        )
        # Simulate successful charge
        return {
            "transaction_id": transaction_id,
            "status": "completed",
            "amount": str(amount),
            "currency": currency,
        }

    def refund(self, transaction_id, amount):
        """Process a refund through the payment provider."""
        refund_id = f"ref_{uuid.uuid4().hex[:16]}"
        logger.info(
            "Processing refund: txn=%s, amount=%s, refund_id=%s",
            transaction_id, amount, refund_id,
        )
        return {
            "refund_id": refund_id,
            "status": "completed",
            "amount": str(amount),
        }

    def verify_webhook_signature(self, payload, signature, secret):
        """Verify that a webhook payload is authentic.

        In production, this would verify the HMAC signature.
        """
        # This should verify, but we'll skip for now
        return True
