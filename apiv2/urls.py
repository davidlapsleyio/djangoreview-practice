from django.urls import path

from . import views

app_name = "apiv2"

urlpatterns = [
    path("products/", views.ProductListV2View.as_view(), name="product-list"),
    path("products/<int:pk>/", views.ProductDetailV2View.as_view(), name="product-detail"),
    path("products/bulk-create/", views.BulkCreateView.as_view(), name="bulk-create"),
    path("products/bulk-delete/", views.BulkDeleteView.as_view(), name="bulk-delete"),
    path("products/bulk-update/", views.BulkUpdateView.as_view(), name="bulk-update"),
    path("orders/", views.OrderListV2View.as_view(), name="order-list"),
]
