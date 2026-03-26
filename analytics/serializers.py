from rest_framework import serializers

from .models import Report


class DashboardRequestSerializer(serializers.Serializer):
    # Issue 5: Date range accepts arbitrary input without validation
    start_date = serializers.CharField(required=False)
    end_date = serializers.CharField(required=False)


class RevenueSerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    order_count = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    top_products = serializers.ListField()


class CohortRequestSerializer(serializers.Serializer):
    period = serializers.ChoiceField(
        choices=["daily", "weekly", "monthly"],
        default="monthly",
    )
    start_date = serializers.CharField(required=False)
    end_date = serializers.CharField(required=False)


class ExportRequestSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(
        choices=["revenue", "orders", "customers", "products"],
    )
    report_format = serializers.ChoiceField(choices=Report.Format.choices)
    start_date = serializers.CharField(required=False)
    end_date = serializers.CharField(required=False)
    email_to = serializers.EmailField(required=False)


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            "id", "title", "report_format", "report_status",
            "parameters", "created_at", "completed_at",
        ]
