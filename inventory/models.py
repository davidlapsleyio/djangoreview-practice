from django.conf import settings
from django.db import models


class InventoryLog(models.Model):
    """Tracks all stock changes for audit purposes."""

    class ChangeType(models.TextChoices):
        SALE = "sale", "Sale"
        RESTOCK = "restock", "Restock"
        ADJUSTMENT = "adjustment", "Manual Adjustment"
        RETURN = "return", "Return"

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="inventory_logs",
    )
    change_type = models.CharField(max_length=20, choices=ChangeType.choices)
    quantity_change = models.IntegerField()  # positive = increase, negative = decrease
    previous_stock = models.PositiveIntegerField()
    new_stock = models.PositiveIntegerField()
    # Issue 5: No pagination, no archiving — grows unbounded
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.change_type}: {self.quantity_change} for {self.product.name}"


class StockAlert(models.Model):
    """Alerts generated when stock drops below threshold."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        RESOLVED = "resolved", "Resolved"

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="stock_alerts",
    )
    threshold = models.PositiveIntegerField(default=10)
    current_stock = models.PositiveIntegerField()
    alert_status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert: {self.product.name} stock at {self.current_stock}"


class ReorderRequest(models.Model):
    """Automatic reorder requests triggered by low stock."""

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="reorder_requests",
    )
    quantity = models.PositiveIntegerField()
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reorder: {self.quantity}x {self.product.name}"
