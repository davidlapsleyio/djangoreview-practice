import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def update_product_stock_cache():
    """Refresh cached stock counts for low-stock alerts."""
    from .models import Product

    low_stock = Product.objects.filter(stock__lte=5, is_active=True)
    count = low_stock.count()
    logger.info("Found %d products with low stock.", count)
    return count
