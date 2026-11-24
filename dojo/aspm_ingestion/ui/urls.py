from django.urls import path

from dojo.aspm_ingestion.ui.views import commit_evidence

urlpatterns = [path("commits/<int:commit_id>/evidence", commit_evidence, name="aspm_commit_evidence")]
