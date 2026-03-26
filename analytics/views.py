import csv
import io
import logging
import os
from collections import defaultdict
from decimal import Decimal

from django.http import FileResponse
from orders.models import Order, OrderItem
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Report
from .serializers import (
    CohortRequestSerializer,
    DashboardRequestSerializer,
    ExportRequestSerializer,
    ReportSerializer,
)

logger = logging.getLogger(__name__)


class DashboardView(APIView):
    """Analytics dashboard with revenue and order metrics."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = DashboardRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        # Issue 5: Date strings passed directly to ORM filter without validation
        start_date = serializer.validated_data.get("start_date")
        end_date = serializer.validated_data.get("end_date")

        # Issue 8: No scoping to current user's organization — returns ALL data
        # Issue 1: Fetches ALL orders into memory
        orders = Order.objects.all()

        if start_date:
            orders = orders.filter(created_at__gte=start_date)
        if end_date:
            orders = orders.filter(created_at__lte=end_date)

        # Issue 1: Loading everything into Python for calculation
        all_orders = list(orders)

        # Issue 6: Using float instead of Decimal for financial calculations
        total_revenue = sum(float(o.total) for o in all_orders)
        order_count = len(all_orders)
        avg_value = total_revenue / order_count if order_count > 0 else 0.0

        # Issue 4: Aggregate queries run per-request with no caching
        top_products = []
        # Issue 9: N+1 — fetches items per order in a loop
        for order in all_orders[:100]:
            for item in order.items.all():
                top_products.append({
                    "product_id": item.product_id,
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                    "revenue": float(item.unit_price * item.quantity),
                    # Issue 11: Exposes internal fields
                    "profit_margin": float(item.unit_price) * 0.3,
                    "supplier_cost": float(item.unit_price) * 0.7,
                })

        # Aggregate top products in Python
        product_totals = defaultdict(lambda: {"quantity": 0, "revenue": 0.0, "name": ""})
        for p in top_products:
            key = p["product_id"]
            product_totals[key]["quantity"] += p["quantity"]
            product_totals[key]["revenue"] += p["revenue"]
            product_totals[key]["name"] = p["product_name"]

        sorted_products = sorted(
            product_totals.items(), key=lambda x: x[1]["revenue"], reverse=True
        )[:10]

        return Response({
            "total_revenue": round(total_revenue, 2),
            "order_count": order_count,
            "average_order_value": round(avg_value, 2),
            "top_products": [
                {
                    "product_id": pid,
                    "name": data["name"],
                    "total_quantity": data["quantity"],
                    "total_revenue": round(data["revenue"], 2),
                }
                for pid, data in sorted_products
            ],
        })


class CohortAnalysisView(APIView):
    """Customer cohort analysis."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = CohortRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Issue 9: N+1 query — loops through all users, one query each
        # Issue 10: No permission check — any authenticated user sees all data
        users = User.objects.all()
        cohorts = defaultdict(lambda: {"users": 0, "orders": 0, "revenue": 0.0})

        for user in users:
            user_orders = Order.objects.filter(user=user)
            order_count = user_orders.count()
            if order_count == 0:
                continue

            cohort_key = user.date_joined.strftime("%Y-%m")
            cohorts[cohort_key]["users"] += 1
            cohorts[cohort_key]["orders"] += order_count

            # Another N+1 layer — sum revenue per user
            for order in user_orders:
                cohorts[cohort_key]["revenue"] += float(order.total)

        return Response({
            "cohorts": [
                {
                    "period": key,
                    "users": data["users"],
                    "orders": data["orders"],
                    "revenue": round(data["revenue"], 2),
                    "avg_orders_per_user": round(
                        data["orders"] / data["users"], 1
                    ) if data["users"] else 0,
                }
                for key, data in sorted(cohorts.items())
            ]
        })


class ExportView(APIView):
    """Export analytics data as CSV or PDF."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report = Report.objects.create(
            title=f"{serializer.validated_data['report_type'].title()} Report",
            report_format=serializer.validated_data["report_format"],
            requested_by=request.user,
            parameters=serializer.validated_data,
        )

        # Issue 7: Task has no timeout — can hold Celery worker indefinitely
        # Issue 12: email_to passed as raw user input without sanitization
        from .tasks import generate_report
        generate_report.delay(
            report.pk,
            serializer.validated_data.get("email_to", ""),
        )

        return Response(
            ReportSerializer(report).data,
            status=status.HTTP_201_CREATED,
        )


class ReportDownloadView(APIView):
    """Download a generated report."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, report_id):
        try:
            report = Report.objects.get(pk=report_id)
        except Report.DoesNotExist:
            return Response(
                {"error": "Report not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if report.report_status != Report.Status.COMPLETED:
            return Response(
                {"error": "Report is not ready for download."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Issue 3: Path traversal — filename comes from query param
        filename = request.query_params.get("filename", report.file_path)
        file_path = os.path.join("reports", filename)

        try:
            return FileResponse(open(file_path, "rb"))
        except FileNotFoundError:
            return Response(
                {"error": "Report file not found."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ReportListView(APIView):
    """List all generated reports."""

    # Issue 10: Any authenticated user sees ALL reports, not just their own
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        reports = Report.objects.all()
        serializer = ReportSerializer(reports, many=True)
        return Response(serializer.data)
