from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("search/", views.ProductSearchView.as_view(), name="product-search"),
    path("stock/", views.StockLevelView.as_view(), name="stock-levels"),
    path("stock/update/", views.StockUpdateView.as_view(), name="stock-update"),
    path(
        "history/<int:product_id>/",
        views.InventoryHistoryView.as_view(),
        name="inventory-history",
    ),
    path("alerts/", views.StockAlertListView.as_view(), name="stock-alerts"),
]
