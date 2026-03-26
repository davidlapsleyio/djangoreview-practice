from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("products", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="InventoryLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("change_type", models.CharField(choices=[("sale", "Sale"), ("restock", "Restock"), ("adjustment", "Manual Adjustment"), ("return", "Return")], max_length=20)),
                ("quantity_change", models.IntegerField()),
                ("previous_stock", models.PositiveIntegerField()),
                ("new_stock", models.PositiveIntegerField()),
                ("notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="inventory_logs", to="products.product")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="StockAlert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("threshold", models.PositiveIntegerField(default=10)),
                ("current_stock", models.PositiveIntegerField()),
                ("alert_status", models.CharField(choices=[("active", "Active"), ("acknowledged", "Acknowledged"), ("resolved", "Resolved")], default="active", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="stock_alerts", to="products.product")),
            ],
        ),
        migrations.CreateModel(
            name="ReorderRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField()),
                ("is_processed", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reorder_requests", to="products.product")),
            ],
        ),
        # Issue 10: Adding cost_price as non-nullable without default
        migrations.AddField(
            model_name="product",
            name="cost_price",
            field=models.DecimalField(decimal_places=2, max_digits=10),
            preserve_default=False,
        ),
    ]
