import hashlib
import json
from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Count, Max
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from rest_framework.exceptions import APIException

from dojo.aspm_ingestion.api.serializer import ReportRequestSerializer
from dojo.aspm_ingestion.queries import compare_observations, completed_observations
from dojo.aspm_ingestion.selection import live_selection
from dojo.aspm_ingestion.services import request_report
from dojo.product.queries import get_authorized_products
from dojo.scm.queries import authorized_commits


@require_GET
def commit_evidence(request, commit_id, *, section=None):
    commit = get_object_or_404(authorized_commits(request.user), pk=commit_id)
    section = section or request.GET.get("tab", "overview")
    try:
        options = {"pipeline": request.GET["pipeline"]} if request.GET.get("pipeline") else {}
        if request.GET.getlist("scan_ids"):
            options = {"scan_ids": request.GET.getlist("scan_ids")}
        selector = ReportRequestSerializer(data=options)
        selector.is_valid(raise_exception=True)
        selection = live_selection(commit, **selector.validated_data)
    except APIException as error:
        return HttpResponseBadRequest(str(error.detail))
    observations = completed_observations(commit, selection).select_related("scan")
    severity = request.GET.get("severity", "")
    if severity in {"Critical", "High", "Medium", "Low", "Info"}:
        observations = observations.filter(severity=severity)
    base = None
    coverage_warning = ""
    base_coverage = target_coverage = None
    category = request.GET.get("category", "new")
    if section == "changes" and request.GET.get("base"):
        try:
            base_id = int(request.GET["base"])
            if not 1 <= base_id <= 2**63 - 1:
                return HttpResponseBadRequest("Invalid base commit.")
        except ValueError:
            return HttpResponseBadRequest("Invalid base commit.")
        base = get_object_or_404(authorized_commits(request.user).filter(repository=commit.repository).exclude(pk=commit.pk), pk=base_id)
        if category not in {"new", "fixed", "unchanged"}:
            category = "new"
        try:
            observations, coverage_warning, base_coverage, target_coverage = compare_observations(
                base, commit, category, severity, base_pipeline=request.GET.get("base_pipeline") or None,
                target_pipeline=request.GET.get("pipeline") or None,
                base_report=request.GET.get("base_report") or None, target_report=request.GET.get("target_report") or None,
            )
        except APIException as error:
            return HttpResponseBadRequest(str(error.detail))
    elif section == "changes":
        observations = observations.none()
    next_url = None
    rows = []
    if section in {"findings", "changes"}:
        try:
            after = int(request.GET.get("after", "0"))
            if not 0 <= after <= 2**63 - 1:
                return HttpResponseBadRequest("Invalid observation cursor.")
        except ValueError:
            return HttpResponseBadRequest("Invalid observation cursor.")
        rows = list(observations.select_related("scan").filter(pk__gt=after).order_by("pk")[:51])
        if len(rows) > 50:
            params = request.GET.copy()
            params["after"] = rows[49].pk
            next_url = "?" + params.urlencode()
        rows = rows[:50]
    nav_params = request.GET.copy()
    for key in ("tab", "after", "page"):
        nav_params.pop(key, None)
    return render(request, "dojo/aspm/commit_evidence.html", {
        "base_reports": base.aspm_reports.filter(status="COMPLETED").order_by("-version")[:100] if base else [],
        "target_reports": commit.aspm_reports.filter(status="COMPLETED").order_by("-version")[:100] if section == "changes" else [],
        "base_pipeline": request.GET.get("base_pipeline", ""),
        "base_report_id": request.GET.get("base_report", ""), "target_report_id": request.GET.get("target_report", ""),
        "taxonomy_preview": list(observations.order_by("pk").values_list("snapshot__cwe", "snapshot__vulnerability_ids")[:20]) if section in {"overview", "reports"} else [],
        "selection": selection, "state_revision": state_revision(commit),
        "nav_params": "&" + nav_params.urlencode() if nav_params else "",
        "can_export": get_authorized_products("edit", user=request.user).filter(pk=commit.repository.product_id).exists(),
        "commit": commit, "section": section, "base_commit": base, "category": category,
        "coverage_warning": coverage_warning, "base_coverage": base_coverage, "target_coverage": target_coverage,
        "scans": Paginator(commit.scan_runs.order_by("-created_at"), 25).get_page(request.GET.get("page")),
        "reports": Paginator(commit.aspm_reports.order_by("-version"), 25).get_page(request.GET.get("page")),
        "observations": rows, "next_url": next_url,
        "scan_statuses": commit.scan_runs.values("status").annotate(total=Count("pk")).order_by("status"),
        "recent_commits": commit.repository.commits.exclude(pk=commit.pk).order_by("-pk")[:100],
    })


def state_revision(commit):
    """Small ScanRun/report aggregates only; never scan FindingObservation for polling."""
    scans = list(commit.scan_runs.values("status").annotate(total=Count("pk"), created=Max("created_at"), finished=Max("finished_at"), started=Max("started_at")).order_by("status"))
    reports = list(commit.aspm_reports.values("status").annotate(total=Count("pk"), version=Max("version")).order_by("status"))
    return hashlib.sha256(json.dumps([scans, reports], default=str, sort_keys=True).encode()).hexdigest()


@require_GET
def commit_state(request, commit_id):
    commit = get_object_or_404(authorized_commits(request.user), pk=commit_id)
    response = JsonResponse({"revision": state_revision(commit)})
    response["Cache-Control"] = "private, no-store"
    return response


@require_POST
def create_report(request, commit_id):
    commit = get_object_or_404(authorized_commits(request.user), pk=commit_id)
    if not get_authorized_products("edit", user=request.user).filter(pk=commit.repository.product_id).exists():
        return HttpResponseForbidden("Product edit permission is required to generate an export.")
    data = {key: request.POST[key] for key in ("pipeline",) if request.POST.get(key)}
    if request.POST.getlist("scan_ids"):
        data = {"scan_ids": request.POST.getlist("scan_ids")}
    serializer = ReportRequestSerializer(data=data)
    if not serializer.is_valid():
        return HttpResponseBadRequest(str(serializer.errors))
    try:
        request_report(commit, **serializer.validated_data)
    except APIException as error:
        return HttpResponseBadRequest(str(error.detail))
    return redirect(reverse("aspm_commit_evidence", args=[commit.pk]) + "?tab=reports&" + urlencode(data, doseq=True))
