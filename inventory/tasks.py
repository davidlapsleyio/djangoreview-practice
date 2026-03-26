import logging

from celery import shared_task

logger = logging.getLogger(__name__)

LOW_STOCK_THRESHOLD = 10


@shared_task
def check_low_stock():
    """Check for low stock products and create alerts.

    Issue 3: Full table scan every 5 minutes instead of smart querying.
    Issue 8: No deduplication — fires alerts for already-alerted items.
    """
    from products.models import Product

    from .models import ReorderRequest, StockAlert

    # Issue 3: Loads ALL products, even those with plenty of stock
    all_products = Product.objects.all()

    for product in all_products:
        if product.stock <= LOW_STOCK_THRESHOLD and product.is_active:
            # Issue 8: Creates alert even if one already exists for this product
            StockAlert.objects.create(
                product=product,
                threshold=LOW_STOCK_THRESHOLD,
                current_stock=product.stock,
            )
            logger.warning(
                "Low stock alert: %s has %d units remaining",
                product.name, product.stock,
            )

            # Trigger reorder if stock is critically low
            if product.stock <= 3:
                # Issue 8: No check if reorder already pending
                ReorderRequest.objects.create(
                    product=product,
                    quantity=50,  # Default reorder quantity
                )
                logger.info("Reorder triggered for %s", product.name)
