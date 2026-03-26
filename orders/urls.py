from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="order-list"),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
]
