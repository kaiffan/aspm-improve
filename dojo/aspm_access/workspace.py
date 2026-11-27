from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, SuspiciousFileOperation
from django.core.management.base import CommandError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.db.utils import DatabaseError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_http_methods
from psycopg import Error as PostgresError
from redis.exceptions import RedisError

from dojo.aspm_access.models import SsoProductGrant
from dojo.aspm_access.permissions import has_capability
from dojo.aspm_ingestion.engagements import can_manage_engagement_policy
from dojo.aspm_ingestion.models import EngagementPolicy, EngagementStrategy, GeneratedReport, ManagedEngagement, ScanRun
from dojo.aspm_ingestion.scanners import SCANNER_FORMATS
from dojo.engagement.models import Engagement
from dojo.management.commands.aspm_preflight import storage_ready
from dojo.operations.health import database_ready, redis_ready
from dojo.product.models import Product
from dojo.product.queries import get_authorized_products
from dojo.product_type.models import Product_Type
from dojo.scm.models import Repository
from dojo.utils import add_breadcrumb


def _page(request, queryset):
    return Paginator(queryset, 25).get_page(request.GET.get("page"))


def _audit(request, obj, action, message):
    LogEntry.objects.create(
        user=request.user, object_id=str(obj.pk), object_repr=str(obj)[:200],
        content_type=ContentType.objects.get_for_model(obj), action_flag=action, change_message=message,
    )


def _product_workspace(request, *, title, template, context_name, show_scan_activity=False):
    query = request.GET.get("q", "").strip()[:150]
    products = get_authorized_products("view", user=request.user)
    product_types = Product_Type.objects.filter(
        pk__in=products.order_by().values("prod_type_id"),
    ).order_by("name", "pk")
    selected_type = request.GET.get("product_type", "")
    if selected_type.isascii() and selected_type.isdecimal() and len(selected_type) <= 18:
        products = products.filter(prod_type_id=int(selected_type))
    products = products.filter(name__icontains=query).select_related("prod_type").order_by("name", "pk")
    show_scan_activity = show_scan_activity and settings.ASPM_INGESTION_ENABLED and settings.ASPM_SCM_HIERARCHY
    if show_scan_activity:
        latest = ScanRun.objects.filter(
            product_id=OuterRef("pk"), commit__repository__product_id=OuterRef("pk"),
        ).order_by("-created_at", "-pk")
        products = products.annotate(
            latest_scan_at=Subquery(latest.values("created_at")[:1]),
            latest_scan_status=Subquery(latest.values("status")[:1]),
        )
    add_breadcrumb(title=title, top_level=True, request=request)
    return render(request, template, {
        context_name: _page(request, products),
        "show_scan_activity": show_scan_activity,
        "query": query,
        "product_types": product_types,
        "selected_type": selected_type,
    })


@require_GET
def projects(request):
    return _product_workspace(
        request, title=_("Projects"), template="dojo/aspm/projects.html", context_name="projects", show_scan_activity=True,
    )


@require_GET
def classic(request):
    return _product_workspace(request, title=_("Classic Workspace"), template="dojo/aspm/classic.html", context_name="products")


def test_scan(test):
    if not settings.ASPM_SCM_HIERARCHY:
        return None
    return ScanRun.objects.filter(test=test, product_id=test.engagement.product_id).only("pk", "commit_id", "scanner", "status").first()


def classic_reader(request, *, children=None, **context):
    add_breadcrumb(request=request, clear=True)
    return render(request, "dojo/aspm/classic_reader.html", {
        "children": _page(request, children) if children is not None else None,
        **context,
    })


@require_GET
def reports(request):
    query = request.GET.get("q", "").strip()[:150]
    products = get_authorized_products("view", user=request.user).filter(name__icontains=query)
    section = request.GET.get("type", "generated")
    if section == "originals" and settings.ASPM_SCM_HIERARCHY and settings.ASPM_INGESTION_ENABLED:
        entries = ScanRun.objects.filter(product__in=products, commit__repository__product__in=products).select_related("product", "commit").only(
            "id", "product__name", "commit__sha", "scanner", "status", "created_at", "original_name",
        ).order_by("-created_at", "-pk")
    elif section == "classic":
        entries = products.order_by("name", "pk")
    else:
        section = "generated"
        entries = GeneratedReport.objects.filter(commit__repository__product__in=products).select_related(
            "commit__repository__product",
        ).only(
            "id", "version", "status", "created_at",
            "commit__sha", "commit__repository__product__name",
        ).order_by("-created_at", "-pk")
    add_breadcrumb(title=_("Reports"), top_level=True, request=request)
    return render(request, "dojo/aspm/reports.html", {"entries": _page(request, entries), "query": query, "section": section})


@require_GET
@login_required
def scan_processing(request):
    if not settings.ASPM_INGESTION_ENABLED or not settings.ASPM_SCM_HIERARCHY:
        raise Http404
    query = request.GET.get("q", "").strip()[:150]
    state = request.GET.get("status", "")
    products = get_authorized_products("view", user=request.user).filter(name__icontains=query)
    entries = ScanRun.objects.filter(product__in=products, commit__repository__product__in=products)
    if state in ScanRun.Status.values:
        entries = entries.filter(status=state)
    entries = entries.select_related("product", "commit").only(
        "id", "product__name", "commit__sha", "scanner", "status", "created_at", "finished_at", "error_code",
    ).order_by("-created_at", "-pk")
    add_breadcrumb(title=_("Scan processing"), top_level=True, request=request)
    return render(request, "dojo/aspm/scan_processing.html", {
        "entries": _page(request, entries), "query": query, "state": state, "states": ScanRun.Status.choices,
    })


@require_GET
@login_required
def system_health(request):
    if not has_capability(request.user, "dojo.view_system_settings"):
        raise PermissionDenied
    cache_url = settings.CACHES["default"].get("LOCATION")

    def storage_available():
        storage_ready(writable=False)
        return True

    probes = [
        (_("PostgreSQL"), database_ready),
        (_("Celery broker"), lambda: redis_ready(settings.CELERY_BROKER_URL)),
        (_("Private storage"), storage_available),
    ]
    if isinstance(cache_url, str) and cache_url.startswith(("redis://", "rediss://")):
        probes.append((_("Cache"), lambda: redis_ready(cache_url)))
    checks = []
    for name, check in probes:
        try:
            available = check()
        except (CommandError, DatabaseError, OSError, PostgresError, RedisError, SuspiciousFileOperation):
            available = False
        checks.append((name, available))
    add_breadcrumb(title=_("System health"), top_level=True, request=request)
    return render(request, "dojo/aspm/system_health.html", {
        "checks": checks, "storage_backend": settings.ASPM_STORAGE_BACKEND,
    })


@require_GET
def scanners(request):
    products = get_authorized_products("view", user=request.user)
    choices = []
    for label, scan_type, file_format in SCANNER_FORMATS:
        last = ScanRun.objects.filter(product__in=products, scanner=scan_type).order_by("-created_at").only(
            "id", "commit_id", "status", "metadata", "error_code", "created_at",
        ).first()
        success = ScanRun.objects.filter(product__in=products, scanner=scan_type, status=ScanRun.Status.COMPLETED).order_by(
            "-finished_at",
        ).only("id", "commit_id", "finished_at").first()
        choices.append((label, scan_type, file_format, last, success))
    return render(request, "dojo/aspm/scanners.html", {"scanners": choices})


class GrantForm(forms.Form):
    group_id = forms.UUIDField(label="Keycloak entitlement ID")
    product = forms.IntegerField(min_value=1, max_value=2**63 - 1, label="Product ID")

    def clean_product(self):
        product = Product.objects.filter(pk=self.cleaned_data["product"]).first()
        if product is None:
            msg = "Choose an existing Product ID."
            raise forms.ValidationError(msg)
        return product


@require_http_methods(["GET", "POST"])
def sso_mappings(request):
    if not settings.ASPM_OIDC_ENABLED:
        raise Http404
    if not has_capability(request.user, "dojo.manage_sso_mapping"):
        raise PermissionDenied
    grants = SsoProductGrant.objects.filter(issuer=settings.ASPM_OIDC_ISSUER)
    form = GrantForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        with transaction.atomic():
            if request.POST.get("action") == "revoke":
                grant = get_object_or_404(grants.select_for_update(), pk=request.POST.get("grant"))
                _audit(request, grant, DELETION, f"Revoked entitlement {grant.group_id} for Product {grant.product_id}.")
                grant.delete()
                return redirect("aspm_sso_mappings")
            if form.is_valid():
                grant, created = grants.get_or_create(issuer=settings.ASPM_OIDC_ISSUER, **form.cleaned_data)
                if created:
                    _audit(request, grant, ADDITION, f"Granted entitlement {grant.group_id} for Product {grant.product_id}.")
                return redirect("aspm_sso_mappings")
    return render(request, "dojo/aspm/sso_mappings.html", {
        "form": form, "grants": _page(request, grants.select_related("product").order_by("product__name", "pk")),
    })


class PolicyForm(forms.Form):
    strategy = forms.ChoiceField(choices=EngagementStrategy.choices)


@require_http_methods(["GET", "POST"])
def engagement_policy(request, product_id):
    if not can_manage_engagement_policy(request.user):
        raise PermissionDenied
    product = get_object_or_404(get_authorized_products("view", user=request.user), pk=product_id)
    repositories = product.repositories.order_by("url", "pk")
    repo_id = request.GET.get("repository", "")
    if repo_id and (not repo_id.isascii() or not repo_id.isdecimal() or len(repo_id) > 18):
        raise Http404
    repository = get_object_or_404(repositories, pk=repo_id) if repo_id else None
    policies = EngagementPolicy.objects.filter(product=product, repository=repository)
    current = policies.first()
    form = PolicyForm(request.POST if request.method == "POST" else None, initial={
        "strategy": current.strategy if current else settings.ASPM_DEFAULT_ENGAGEMENT_POLICY,
    })
    assignments = ManagedEngagement.objects.filter(repository__product=product)
    if repository:
        assignments = assignments.filter(repository=repository)
    if request.method == "POST":
        destination = request.get_full_path()
        with transaction.atomic():
            action = request.POST.get("action")
            if action == "archive":
                binding = get_object_or_404(assignments, pk=request.POST.get("binding"))
                Repository.objects.select_for_update(no_key=True).get(pk=binding.repository_id)
                Engagement.objects.select_for_update(no_key=True).get(pk=binding.engagement_id)
                if assignments.filter(pk=binding.pk, archived_at__isnull=True).update(archived_at=timezone.now()):
                    _audit(request, product, CHANGE, f"Engagement policy: archived Engagement {binding.engagement_id} for Repository {binding.repository_id}.")
                return redirect(destination)
            if action == "inherit":
                policy = policies.select_for_update().first()
                if policy:
                    _audit(request, product, CHANGE, f"Engagement policy: removed override for Repository {repo_id or 'all'}.")
                    policy.delete()
                return redirect(destination)
            if form.is_valid():
                policy, _ = policies.update_or_create(product=product, repository=repository, defaults=form.cleaned_data)
                _audit(request, product, CHANGE,
                       f"Engagement policy: set {policy.strategy} for Repository {repo_id or 'all'}.")
                messages.success(request, "Engagement policy saved.")
                return redirect(destination)
    assignments = assignments.select_related("repository", "engagement").annotate(
        last_test=Subquery(ScanRun.objects.filter(engagement_id=OuterRef("engagement_id"), test_id__isnull=False)
                           .order_by("-created_at").values("test_id")[:1]),
    ).order_by("-pk")
    audit = LogEntry.objects.filter(
        content_type=ContentType.objects.get_for_model(Product), object_id=str(product.pk),
        change_message__startswith="Engagement policy:",
    ).select_related("user").order_by("-action_time")[:25]
    return render(request, "dojo/aspm/engagement_policy.html", {
        "form": form, "product": product, "repository": repository, "repositories": repositories[:100],
        "current": current, "assignments": _page(request, assignments), "audit": audit,
    })
