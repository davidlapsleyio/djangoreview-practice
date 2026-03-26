from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "products"

router = DefaultRouter()
router.register("", views.ProductViewSet, basename="product")

urlpatterns = [
    path("listing/", views.product_listing, name="product-listing"),
    path("", include(router.urls)),
]
