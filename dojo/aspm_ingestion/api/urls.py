from django.urls import path
from drf_spectacular.views import SpectacularAPIView

from dojo.aspm_ingestion.api import views
from dojo.aspm_ingestion.schema import ASPM_SCHEMA_SETTINGS

app_name = "aspm_v1"
urlpatterns = [
    path("openapi/", SpectacularAPIView.as_view(urlconf="dojo.aspm_ingestion.schema_urls", custom_settings=ASPM_SCHEMA_SETTINGS), name="openapi"),
    path("scans/", views.ScanUploadView.as_view(), name="scans"),
    path("scans/<uuid:pk>/", views.ScanDetailView.as_view(), name="scan-detail"),
    path("scans/<uuid:pk>/retry/", views.ScanRetryView.as_view(), name="scan-retry"),
    path("scans/<uuid:pk>/artifact/", views.ArtifactDownloadView.as_view(), name="artifact"),
    path("projects/<int:pk>/repositories/", views.ProjectRepositoriesView.as_view(), name="repositories"),
    path("repositories/<int:pk>/commits/", views.RepositoryCommitsView.as_view(), name="commits"),
    path("commits/<int:pk>/scans/", views.CommitScansView.as_view(), name="commit-scans"),
    path("commits/<int:pk>/finalize/", views.FinalizeView.as_view(), name="finalize"),
    path("commits/<int:pk>/reports/", views.CommitReportsView.as_view(), name="reports"),
    path("reports/<uuid:pk>/download/", views.ReportDownloadView.as_view(), name="report-download"),
]
