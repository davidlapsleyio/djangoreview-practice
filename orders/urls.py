from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="order-list"),
    path("bulk-update/", views.BulkOrderUpdateView.as_view(), name="bulk-order-update"),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("<int:pk>/update/", views.OrderUpdateView.as_view(), name="order-update"),
    path("<int:order_pk>/items/", views.OrderItemCreateView.as_view(), name="order-item-create"),
]
