from django.conf import settings
from django.http import HttpResponseNotFound, JsonResponse

from dojo.aspm_access.permissions import role
from dojo.aspm_ingestion.engagements import can_manage_engagement_policy
from dojo.aspm_ingestion.object_store import ObjectUnavailableError
from dojo.aspm_ingestion.permissions import api_only_scans_enabled
from dojo.webhooks.permissions import can_manage_webhooks


class ApiOnlyScansMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        match = request.resolver_match
        if api_only_scans_enabled() and match and match.url_name in {
            "import_scan_results_prod", "import_scan_results", "re_import_scan_results",
        }:
            return HttpResponseNotFound("Scanner results are accepted through the REST API only.")
        return None


def ingestion_context(request):
    return {
        "aspm_api_only": api_only_scans_enabled(),
        "aspm_ingestion_enabled": settings.ASPM_INGESTION_ENABLED and settings.ASPM_SCM_HIERARCHY,
        "aspm_oidc_enabled": settings.ASPM_OIDC_ENABLED,
        "aspm_role": role(request.user),
        "aspm_can_manage_engagements": can_manage_engagement_policy(request.user),
        "aspm_webhooks_can_manage": settings.ASPM_WEBHOOKS_ENABLED and can_manage_webhooks(request.user),
    }


class PrivateStorageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, ObjectUnavailableError):
            return JsonResponse({"detail": "Private storage is temporarily unavailable."}, status=503)
        return None
