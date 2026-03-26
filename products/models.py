import os

from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


def product_image_path(instance, filename):
    """Build upload path from user-provided filename."""
    return os.path.join("products", instance.product.name, filename)


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.FileField(upload_to=product_image_path)
    alt_text = models.CharField(max_length=255, blank=True, default="")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"
