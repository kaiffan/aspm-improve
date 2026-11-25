import time

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, logout
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

from dojo.aspm_access.backend import BACKEND

SESSION_KEY = "aspm_oidc_access"
FLOW_KEY = "aspm_oidc_flow"

READ_ROUTES = frozenset({
    "aspm_projects", "aspm_reports", "scm_repository_list", "scm_repository_detail", "scm_commit_detail", "scm_commit_compare",
    "aspm_commit_evidence", "aspm_commit_state", "aspm_scanners", "view_profile",
    "aspm_v1:repositories", "aspm_v1:commits", "aspm_v1:commit-scans", "aspm_v1:scan-detail",
    "aspm_v1:artifact", "aspm_v1:reports", "aspm_v1:report-download",
    "product-list", "product-detail", "repository-list", "repository-detail", "commit-list", "commit-detail",
    "api_v3:assets_list", "api_v3:assets_detail",
})
CLASSIC_READ_ROUTES = frozenset({
    "aspm_classic", "product_type", "view_product_type", "product", "view_product", "view_engagement",
    "view_engagements", "view_test", "view_finding", "product_report", "engagement_report", "test_report",
    "product_findings_report", "view_product_metrics", "async_burndown_metrics",
    "engagement-list", "engagement-detail", "test-list", "test-detail",
    "test_imports-list", "test_imports-detail", "product-stats",
    "api_v3:engagements_list", "api_v3:engagements_detail", "api_v3:tests_list", "api_v3:tests_detail",
})
CLASSIC_REPORT_API = {"product-generate-report", "engagement-generate-report", "test-generate-report"}

EXPERT_READ_ROUTES = READ_ROUTES | CLASSIC_READ_ROUTES | {
    "engagement", "all_engagements", "active_engagements", "engagements_all",
    "report_builder", "product_type_report", "report_findings", "quick_report",
    "product_type-list", "product_type-detail", "api_v3:organizations_list", "api_v3:organizations_detail",
    "download_finding_pic",

    "dashboard", "all_findings", "open_findings", "verified_findings", "closed_findings", "accepted_findings",
    "product_all_findings", "product_open_findings", "product_false_positive_findings",
    "view_finding", "view_test", "view_product", "close_finding", "verify_finding", "finding-list", "finding-detail",
    "api_v3:findings_list", "api_v3:findings_detail", "api_v3:findings_export_csv", "api_v3:findings_notes_list",
}
EXPERT_ACTIONS = {
    "aspm_create_report": {"POST"},
    "finding-detail": {"PATCH"},
    "api_v3:findings_detail": {"PATCH"},
    "api_v3:findings_update": {"PATCH"},
    "finding-close": {"POST"},
    "close_finding": {"POST"},
    "verify_finding": {"POST"},
    "reopen_finding": {"POST"},
    "finding-reopen": {"POST"},
    "finding-verify": {"POST"},
    "finding-notes": {"GET", "HEAD", "POST"},
    "new_eng_for_prod": {"GET", "POST"},
    "new_eng_for_prod_cicd": {"GET", "POST"},
    "add_tests": {"GET", "POST"},
    "edit_engagement": {"GET", "POST"},
    "edit_test": {"GET", "POST"},
    "add_findings": {"GET", "POST"},
    "view_engagement": {"POST"},
    "view_test": {"POST"},
    "view_finding": {"POST"},
    "engagement-list": {"POST"},
    "engagement-detail": {"PUT", "PATCH"},
    "test-list": {"POST"},
    "test-detail": {"PUT", "PATCH"},
    "finding-list": {"POST"},
    "importscan-list": {"POST"},
    "reimportscan-list": {"POST"},
    "custom_report": {"POST"},
    "product_type-generate-report": {"POST"},
    "api_v3:engagements_list": {"POST"},
    "api_v3:engagements_create": {"POST"},
    "api_v3:engagements_detail": {"PUT", "PATCH"},
    "api_v3:engagements_update": {"PATCH"},
    "api_v3:engagements_replace": {"PUT"},
    "api_v3:tests_list": {"POST"},
    "api_v3:tests_create": {"POST"},
    "api_v3:tests_detail": {"PUT", "PATCH"},
    "api_v3:tests_update": {"PATCH"},
    "api_v3:tests_replace": {"PUT"},
    "api_v3:findings_create": {"POST"},
    "api_v3:findings_list": {"POST"},
    "api_v3:import": {"POST"},
}
AUTH_ROUTES = {"aspm_oidc_login", "aspm_oidc_callback", "aspm_oidc_logout"}


class ManagedSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.session.get(BACKEND_SESSION_KEY) != BACKEND:
            return None
        if not request.user.is_authenticated:
            logout(request)
            return None
        identity = request.user.aspm_sso_identity
        access = request.session.get(SESSION_KEY)
        if (
            not settings.ASPM_OIDC_ENABLED or request.user.has_usable_password()
            or not access or identity.issuer != settings.ASPM_OIDC_ISSUER or identity.issuer != access.get("issuer")
            or time.time() >= min(access["expires"], access["checked"] + settings.ASPM_OIDC_GROUP_TTL)
        ):
            logout(request)
            if request.path_info.lstrip("/").startswith(("api/", f"{settings.URL_PREFIX}api/")):
                return HttpResponseForbidden()
            return None
        request.user._aspm_principal = access
        return None

    def process_view(self, request, view_func, view_args, view_kwargs):
        access = getattr(request.user, "_aspm_principal", None)
        if access is None:
            return None
        route = request.resolver_match.view_name
        if route in AUTH_ROUTES:
            return None
        if route in {"api-token-auth", "api_v2_key", "api-token-revoke", "logout"}:
            return HttpResponseForbidden()
        if access["role"] == "secops":
            return None
        if request.method in {"GET", "HEAD"}:
            route = getattr(view_func, "redirect_view_name", route)
        if request.method == "POST" and route in CLASSIC_REPORT_API:
            return None
        read = EXPERT_READ_ROUTES if access["role"] == "expert" else READ_ROUTES | CLASSIC_READ_ROUTES
        if request.method in {"GET", "HEAD", "OPTIONS"} and route in read:
            return None
        if access["role"] == "expert" and request.method in EXPERT_ACTIONS.get(route, ()):
            return None
        return HttpResponseForbidden()
