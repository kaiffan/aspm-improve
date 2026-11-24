from django.urls import path

from dojo.aspm_ingestion.ui.views import commit_evidence, commit_state, create_report

urlpatterns = [
    path("commits/<int:commit_id>/evidence", commit_evidence, name="aspm_commit_evidence"),
    path("commits/<int:commit_id>/evidence/state", commit_state, name="aspm_commit_state"),
    path("commits/<int:commit_id>/evidence/reports", create_report, name="aspm_create_report"),
]
