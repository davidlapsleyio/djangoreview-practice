from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/products/", include("products.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/users/", include("users.urls")),
    path("api/reviews/", include("reviews.urls")),
    path("api/analytics/", include("analytics.urls")),
]
