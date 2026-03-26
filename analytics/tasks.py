import csv
import io
import logging

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def generate_report(report_id, email_to=""):
    """Generate a report and optionally email it.

    Issue 2: No row limit — can OOM on large datasets.
    Issue 7: No timeout — can hold Celery worker indefinitely.
    Issue 12: email_to used without sanitization in send_mail.
    """
    from orders.models import Order, OrderItem

    from .models import Report

    try:
        report = Report.objects.get(pk=report_id)
        report.report_status = Report.Status.GENERATING
        report.save()

        params = report.parameters
        start_date = params.get("start_date")
        end_date = params.get("end_date")

        # Build queryset
        orders = Order.objects.all()
        if start_date:
            orders = orders.filter(created_at__gte=start_date)
        if end_date:
            orders = orders.filter(created_at__lte=end_date)

        # Issue 2: No limit — loads ALL orders for CSV generation
        output = io.StringIO()
        writer = csv.writer(output)

        if params.get("report_type") == "orders":
            writer.writerow([
                "Order ID", "User", "Status", "Total", "Date",
                # Issue 11: Internal fields in export
                "Profit Margin", "Supplier Cost",
            ])
            for order in orders.iterator():
                writer.writerow([
                    order.pk,
                    order.user.username,
                    order.status,
                    str(order.total),
                    order.created_at.isoformat(),
                    str(float(order.total) * 0.3),
                    str(float(order.total) * 0.7),
                ])
        elif params.get("report_type") == "revenue":
            writer.writerow(["Date", "Revenue", "Order Count"])
            # Simplified — just dump all orders
            for order in orders.iterator():
                writer.writerow([
                    order.created_at.date().isoformat(),
                    str(order.total),
                    1,
                ])
        elif params.get("report_type") == "customers":
            from django.contrib.auth import get_user_model
            User = get_user_model()
            writer.writerow([
                "User ID", "Username", "Email", "Total Orders", "Total Spent",
            ])
            for user in User.objects.all():
                user_orders = Order.objects.filter(user=user)
                total_spent = sum(float(o.total) for o in user_orders)
                writer.writerow([
                    user.pk,
                    user.username,
                    user.email,
                    user_orders.count(),
                    str(round(total_spent, 2)),
                ])

        # Save report file
        file_path = f"reports/report_{report.pk}.csv"
        report.file_path = file_path
        report.report_status = Report.Status.COMPLETED
        report.completed_at = timezone.now()
        report.save()

        # Issue 12: Raw user email input used in send_mail
        if email_to:
            send_mail(
                subject=f"Your report is ready: {report.title}",
                message=f"Download your report at /api/analytics/reports/{report.pk}/download/",
                from_email="reports@shopify-lite.example.com",
                recipient_list=[email_to],
            )

        logger.info("Report #%s generated successfully", report_id)

    except Exception as e:
        logger.error("Failed to generate report #%s: %s", report_id, e)
        try:
            report = Report.objects.get(pk=report_id)
            report.report_status = Report.Status.FAILED
            report.save()
        except Report.DoesNotExist:
            pass
