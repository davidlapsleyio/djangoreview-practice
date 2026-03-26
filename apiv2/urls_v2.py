"""Alternative URLconf used when X-API-Version: v2 header is sent.

Issue 12: This silently changes field names and behavior without
deprecation warnings or migration path.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/products/", include("apiv2.urls")),
    path("api/orders/", include("apiv2.urls")),
    path("api/users/", include("users.urls")),
    path("api/reviews/", include("reviews.urls")),
]
