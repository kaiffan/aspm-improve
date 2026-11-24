from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from dojo.aspm_ingestion.queries import compare_observations, completed_observations
from dojo.scm.queries import authorized_commits


@require_GET
def commit_evidence(request, commit_id, *, section=None):
    commit = get_object_or_404(authorized_commits(request.user), pk=commit_id)
    section = section or request.GET.get("tab", "overview")
    observations = completed_observations(commit).select_related("scan")
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
        observations, coverage_warning, base_coverage, target_coverage = compare_observations(base, commit, category, severity)
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
            next_url = "?" + urlencode(params)
        rows = rows[:50]
    return render(request, "dojo/aspm/commit_evidence.html", {
        "commit": commit, "section": section, "base_commit": base, "category": category,
        "coverage_warning": coverage_warning, "base_coverage": base_coverage, "target_coverage": target_coverage,
        "scans": Paginator(commit.scan_runs.order_by("-created_at"), 25).get_page(request.GET.get("page")),
        "reports": Paginator(commit.aspm_reports.order_by("-version"), 25).get_page(request.GET.get("page")),
        "observations": rows, "next_url": next_url,
        "scan_statuses": commit.scan_runs.values("status").annotate(total=Count("pk")).order_by("status"),
        "recent_commits": commit.repository.commits.exclude(pk=commit.pk).order_by("-pk")[:100],
    })
