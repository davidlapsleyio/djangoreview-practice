from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "products"

router = DefaultRouter()
router.register("", views.ProductViewSet, basename="product")

urlpatterns = [
    path("<int:product_id>/images/upload/", views.upload_product_image, name="upload-image"),
    path("images/<path:path>", views.serve_product_image, name="serve-image"),
    path("", include(router.urls)),
]
