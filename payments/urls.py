from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("charge/", views.ChargeView.as_view(), name="charge"),
    path("<int:payment_id>/", views.PaymentDetailView.as_view(), name="payment-detail"),
    path("<int:payment_id>/refund/", views.RefundView.as_view(), name="refund"),
    path("webhook/", views.WebhookView.as_view(), name="webhook"),
]
