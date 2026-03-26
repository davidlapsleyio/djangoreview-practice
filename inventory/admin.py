from django.contrib import admin

from .models import InventoryLog, ReorderRequest, StockAlert


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ["product", "change_type", "quantity_change", "created_at"]
    list_filter = ["change_type"]


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ["product", "current_stock", "threshold", "alert_status", "created_at"]
    list_filter = ["alert_status"]


@admin.register(ReorderRequest)
class ReorderRequestAdmin(admin.ModelAdmin):
    list_display = ["product", "quantity", "is_processed", "created_at"]
    list_filter = ["is_processed"]
