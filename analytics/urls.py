from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("cohort/", views.CohortAnalysisView.as_view(), name="cohort-analysis"),
    path("export/", views.ExportView.as_view(), name="export"),
    path(
        "reports/<int:report_id>/download/",
        views.ReportDownloadView.as_view(),
        name="report-download",
    ),
    path("reports/", views.ReportListView.as_view(), name="report-list"),
]
