from django.contrib import admin

from .models import Payment, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "user", "amount", "payment_status", "created_at"]
    list_filter = ["payment_status", "currency"]
    search_fields = ["provider_transaction_id"]


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ["id", "payment", "amount", "refund_status", "created_at"]
    list_filter = ["refund_status"]
