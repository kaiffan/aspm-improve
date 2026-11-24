"""Historical comparisons use the latest explicit pipeline set and comparable coverage."""

from django.db.models import Exists, F, OuterRef

from dojo.aspm_ingestion.models import FindingObservation, ScanRun


def completed_observations(commit):
    return FindingObservation.objects.filter(scan__commit=commit, scan__status=ScanRun.Status.COMPLETED, generation=F("scan__observation_generation"))


def finalized_coverage(commit):
    scan_set = commit.scan_sets.order_by("-created_at", "-pk").first()
    if scan_set is None:
        return {"set": None, "complete": False, "completed_ids": [], "scopes": set()}
    scans = list(commit.scan_runs.filter(pk__in=scan_set.scan_ids).values("pk", "scanner", "status", "metadata"))
    completed = [scan for scan in scans if scan["status"] == ScanRun.Status.COMPLETED]
    missing = set(scan_set.expected_scanners) - {scan["scanner"] for scan in completed}
    return {
        "set": scan_set, "complete": bool(scans) and len(scans) == len(scan_set.scan_ids) and len(completed) == len(scans) and not missing,
        "completed_ids": [scan["pk"] for scan in completed],
        "scopes": {(scan["scanner"], scan["metadata"].get("scan_scope", "")) for scan in scans},
    }


def compare_observations(base, target, category, severity=""):
    before_coverage, after_coverage = finalized_coverage(base), finalized_coverage(target)
    before = completed_observations(base).filter(scan_id__in=before_coverage["completed_ids"])
    after = completed_observations(target).filter(scan_id__in=after_coverage["completed_ids"])
    warning = ""
    if not before_coverage["complete"] or not after_coverage["complete"]:
        warning = "Coverage is incomplete. Missing, failed, running or unfinalized scans cannot establish that a finding is fixed."
    elif before_coverage["scopes"] != after_coverage["scopes"]:
        warning = "Scan scopes differ. Absence cannot establish that a finding is fixed."
    elif any(not scope for scanner, scope in before_coverage["scopes"]):
        warning = "Scan scope is not declared. Absence cannot establish that a finding is fixed."
    source, other = (before, after) if category == "fixed" else (after, before)
    if category == "fixed" and warning:
        source = source.none()
    rows = source.annotate(in_other=Exists(other.filter(identity=OuterRef("identity")))).filter(in_other=category == "unchanged")
    if severity in {"Critical", "High", "Medium", "Low", "Info"}:
        rows = rows.filter(severity=severity)
    return rows, warning, before_coverage, after_coverage
