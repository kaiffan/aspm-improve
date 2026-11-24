from django.http import HttpResponseNotFound

from dojo.aspm_ingestion.permissions import api_only_scans_enabled


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
    return {"aspm_api_only": api_only_scans_enabled()}
