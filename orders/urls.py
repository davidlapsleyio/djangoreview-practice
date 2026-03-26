from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.OrderListView.as_view(), name="order-list"),
    path("dashboard/", views.dashboard_stats, name="dashboard-stats"),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
]
