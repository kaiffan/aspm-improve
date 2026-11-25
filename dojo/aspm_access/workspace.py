from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_http_methods

from dojo.aspm_access.models import SsoProductGrant
from dojo.aspm_access.permissions import has_capability
from dojo.aspm_ingestion.engagements import can_manage_engagement_policy
from dojo.aspm_ingestion.models import EngagementPolicy, EngagementStrategy, GeneratedReport, ManagedEngagement, ScanRun
from dojo.aspm_ingestion.scanners import SCANNER_FORMATS
from dojo.engagement.models import Engagement
from dojo.product.models import Product
from dojo.product.queries import get_authorized_products
from dojo.scm.models import Repository
from dojo.utils import add_breadcrumb


def _page(request, queryset):
    return Paginator(queryset, 25).get_page(request.GET.get("page"))


def _audit(request, obj, action, message):
    LogEntry.objects.create(
        user=request.user, object_id=str(obj.pk), object_repr=str(obj)[:200],
        content_type=ContentType.objects.get_for_model(obj), action_flag=action, change_message=message,
    )


@require_GET
def projects(request):
    query = request.GET.get("q", "").strip()[:150]
    products = get_authorized_products("view", user=request.user).filter(name__icontains=query).order_by("name", "pk")
    add_breadcrumb(title=_("Projects"), request=request)
    return render(request, "dojo/aspm/projects.html", {"projects": _page(request, products), "query": query})


@require_GET
def classic(request):
    query = request.GET.get("q", "").strip()[:150]
    products = get_authorized_products("view", user=request.user).filter(
        name__icontains=query,
    ).select_related("prod_type").order_by("name", "pk")
    add_breadcrumb(title=_("Classic Workspace"), request=request)
    return render(request, "dojo/aspm/classic.html", {"products": _page(request, products), "query": query})


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
    reports = GeneratedReport.objects.filter(
        commit__repository__product__in=products,
    ).select_related("commit__repository__product").only(
        "id", "version", "status", "created_at",
        "commit__sha", "commit__repository__url", "commit__repository__product__name",
    ).order_by("-created_at", "-pk")
    return render(request, "dojo/aspm/reports.html", {"reports": _page(request, reports), "query": query})


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
