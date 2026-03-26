import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopify_lite.settings")

app = Celery("shopify_lite")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
