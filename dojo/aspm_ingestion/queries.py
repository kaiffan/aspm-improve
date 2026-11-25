"""Historical comparisons use selected immutable evidence and comparable coverage."""

from uuid import UUID

from django.db.models import CharField, Exists, F, OuterRef, Value
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Coalesce
from rest_framework.exceptions import ValidationError

from dojo.aspm_ingestion.models import FindingObservation, ScanRun
from dojo.aspm_ingestion.selection import live_selection, scan_contexts


def completed_observations(commit, selection=None):
    selection = live_selection(commit) if selection is None else selection
    return FindingObservation.objects.filter(scan__commit=commit, scan_id__in=selection["completed_ids"], scan__status=ScanRun.Status.COMPLETED, generation=F("scan__observation_generation"))


def finalized_coverage(commit, *, pipeline=None, report_id=None):
    """Compatibility name: live results, or an explicitly requested immutable report version."""
    if report_id is None:
        selection = live_selection(commit, pipeline=pipeline)
        selection["set"] = None
        return selection
    try:
        identifier = UUID(str(report_id))
    except (ValueError, TypeError, AttributeError) as error:
        msg = "Choose a valid report UUID."
        raise ValidationError(msg) from error
    report = commit.aspm_reports.filter(pk=identifier, status=ScanRun.Status.COMPLETED).first()
    if report is None:
        msg = "Choose a completed report belonging to this commit."
        raise ValidationError(msg)
    completed = [row for row in report.manifest["scans"] if row["status"] == ScanRun.Status.COMPLETED]
    identifiers = [row["id"] for row in completed]
    contexts = list(scan_contexts(commit).filter(pk__in=identifiers).order_by("pipeline").values_list("pipeline", flat=True).distinct()[:2])
    return {
        "set": report.scan_set_id, "report": report, "complete": report.manifest["complete"] and len(contexts) == 1,
        "pipeline": contexts[0] if len(contexts) == 1 else None,
        "completed_ids": identifiers,
        "scopes": {(row["scanner"], row["metadata"].get("environment", ""), row["metadata"].get("scan_scope", "")) for row in completed},
    }


def compare_observations(base, target, category, severity="", *, base_pipeline=None, target_pipeline=None, base_report=None, target_report=None):
    before_coverage, after_coverage = finalized_coverage(base, pipeline=base_pipeline, report_id=base_report), finalized_coverage(target, pipeline=target_pipeline, report_id=target_report)
    before = completed_observations(base, before_coverage)
    after = completed_observations(target, after_coverage)
    warning = ""
    if not before_coverage["complete"] or not after_coverage["complete"]:
        warning = "Coverage is incomplete. UNKNOWN / NOT SCANNED / INCOMPLETE: missing, failed, running or undeclared scans cannot establish that a finding is fixed."
    elif before_coverage["pipeline"] != after_coverage["pipeline"]:
        warning = "Pipeline identities differ. UNKNOWN: absence cannot establish that a finding is fixed."
    elif before_coverage["scopes"] != after_coverage["scopes"]:
        warning = "Scan scopes differ. Absence cannot establish that a finding is fixed."
    elif any(not scope for _, _, scope in before_coverage["scopes"]):
        warning = "Scan scope is not declared. Absence cannot establish that a finding is fixed."
    source, other = (before, after) if category == "fixed" else (after, before)
    if category == "fixed" and warning:
        source = source.none()
    environment = Coalesce(KeyTextTransform("environment", "scan__metadata"), Value(""), output_field=CharField())
    corresponding = other.alias(comparison_environment=environment).filter(
        identity=OuterRef("identity"), scan__scanner=OuterRef("scan__scanner"),
        scan__metadata__scan_scope=OuterRef("scan__metadata__scan_scope"),
        comparison_environment=OuterRef("comparison_environment"),
    )
    rows = source.alias(comparison_environment=environment).filter(Exists(corresponding) if category == "unchanged" else ~Exists(corresponding))
    if severity in {"Critical", "High", "Medium", "Low", "Info"}:
        rows = rows.filter(severity=severity)
    return rows, warning, before_coverage, after_coverage
