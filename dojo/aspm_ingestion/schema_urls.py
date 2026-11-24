from django.urls import include, path

urlpatterns = [path("api/aspm/v1/", include("dojo.aspm_ingestion.api.urls"))]
