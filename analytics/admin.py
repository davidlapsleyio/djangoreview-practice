from django.contrib import admin

from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["title", "report_format", "report_status", "requested_by", "created_at"]
    list_filter = ["report_format", "report_status"]
    search_fields = ["title"]
