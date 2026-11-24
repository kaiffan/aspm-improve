"""Bounded live selection. Completed rows are immutable; no observations are aggregated here."""
from collections import Counter

from django.db.models import Case, CharField, Count, F, IntegerField, Value, When
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast, Coalesce, Concat, NullIf
from rest_framework.exceptions import ValidationError

from dojo.aspm_ingestion.models import ScanRun

MAX_SELECTION = 1000
SCAN_FIELDS = ("id", "scanner", "status", "observation_generation", "artifact_sha256", "artifact_size",
               "finding_count", "severity_summary", "error_code", "metadata", "created_at", "finished_at")


def scan_contexts(commit):
    return commit.scan_runs.annotate(
        pipeline=Case(
            When(metadata__pipeline_id__isnull=False, then=Concat(Value("pipeline:"), Cast(KeyTextTransform("pipeline_id", "metadata"), CharField()))),
            When(metadata__build_id__isnull=False, then=Concat(Value("build:"), Cast(KeyTextTransform("build_id", "metadata"), CharField()))),
            default=Concat(Value("legacy:"), Cast("submitted_by_id", CharField())), output_field=CharField(),
        ),
        scope=Coalesce(Cast(KeyTextTransform("scan_scope", "metadata"), CharField()), Value("")),
        job=Coalesce(Cast(KeyTextTransform("job_id", "metadata"), CharField()), Value("")),
        ci_attempt=Cast(Coalesce(NullIf(Cast(KeyTextTransform("attempt_number", "metadata"), CharField()), Value("")), Value("1")), output_field=IntegerField()),
    )


def live_selection(commit, *, pipeline=None, scan_ids=None, expected_scanners=None):
    """
    Choose one successful run per scanner/scope in one explicit pipeline context.

    CI attempt precedes completion time, acceptance time and UUID in descending order.
    A newer unsuccessful attempt never hides the last success, but prevents complete coverage.
    Multiple pipeline contexts require a choice. Explicit IDs are an alternative to a context.
    """
    qs = scan_contexts(commit)
    contexts = list(qs.order_by("pipeline").values_list("pipeline", flat=True).distinct()[:101])
    if scan_ids is not None:
        identifiers = {str(pk) for pk in scan_ids}
        if not identifiers or len(identifiers) > MAX_SELECTION:
            msg = "Select between 1 and 1000 ScanRuns."
            raise ValidationError(msg)
        latest = list(qs.filter(pk__in=identifiers).order_by("scanner", "scope", "pk").values(*SCAN_FIELDS, "pipeline", "scope"))
        if len(latest) != len(identifiers) or any(row["status"] != ScanRun.Status.COMPLETED for row in latest):
            msg = "All selected ScanRuns must be COMPLETED and belong to this commit."
            raise ValidationError(msg)
        selected_contexts = {row["pipeline"] for row in latest}
        if len(selected_contexts) != 1:
            msg = "Choose ScanRuns from one pipeline context."
            raise ValidationError(msg)
        pipeline = selected_contexts.pop()
        slots = {(row["scanner"], row["scope"]) for row in latest}
        if len(slots) != len(latest):
            msg = "Select only one run per scanner and scan scope."
            raise ValidationError(msg)
        completed = latest
    else:
        if pipeline is None and len(contexts) == 1:
            pipeline = contexts[0]
        if pipeline is None and contexts:
            return _summary([], [], contexts, None, expected_scanners, ambiguous=True)
        if pipeline is not None and not qs.filter(pipeline=pipeline).exists():
            msg = "Unknown pipeline context for this commit."
            raise ValidationError(msg)
        qs = qs.filter(pipeline=pipeline) if pipeline is not None else qs.none()
        if qs.values("scanner", "scope", "ci_attempt").annotate(jobs=Count("job", distinct=True)).filter(jobs__gt=1).exists():
            return _summary([], [], contexts, pipeline, expected_scanners, ambiguous=True)
        order = ("scanner", "scope", "-ci_attempt", F("finished_at").desc(nulls_last=True), "-created_at", "-pk")
        latest = list(qs.order_by("scanner", "scope", "-ci_attempt", "-created_at", "-pk").distinct("scanner", "scope").values(*SCAN_FIELDS, "pipeline", "scope")[:MAX_SELECTION + 1])
        completed = list(qs.filter(status=ScanRun.Status.COMPLETED).order_by(*order).distinct("scanner", "scope").values(*SCAN_FIELDS, "pipeline", "scope")[:MAX_SELECTION + 1])
        if len(latest) > MAX_SELECTION or len(completed) > MAX_SELECTION:
            msg = "More than 1000 scan scopes; select a bounded set of scan_ids."
            raise ValidationError(msg)
    # Legacy expected-scanner declarations remain useful only for exactly this selected set.
    # They never pin live visibility or let an old pipeline mask a new one.
    declarations = {tuple(sorted(row["metadata"]["expected_scanners"])) for row in latest if row["metadata"].get("expected_scanners")}
    conflict = len(declarations) > 1
    if expected_scanners is None and declarations:
        expected_scanners = sorted({scanner for declaration in declarations for scanner in declaration})
    if expected_scanners is None:
        frozen = commit.scan_sets.order_by("-created_at", "-pk").first()
        if frozen and set(frozen.scan_ids) == {str(row["id"]) for row in latest}:
            expected_scanners = frozen.expected_scanners
    result = _summary(completed, latest, contexts, pipeline, expected_scanners, conflict=conflict)
    result["explicit_ids"] = [str(row["id"]) for row in completed] if scan_ids is not None else []
    return result


def _summary(completed, latest, contexts, pipeline, expected, *, ambiguous=False, conflict=False):
    severity = Counter()
    for row in completed:
        severity.update(row["severity_summary"])
    known = bool(expected)
    missing = sorted(set(expected or []) - {row["scanner"] for row in completed})
    incomplete = conflict or bool(missing) or any(row["status"] != ScanRun.Status.COMPLETED for row in latest)
    return {
        "scans": completed, "latest": latest, "completed_ids": [row["id"] for row in completed],
        "contexts": contexts[:100], "contexts_truncated": len(contexts) > 100,
        "pipeline": pipeline, "ambiguous": ambiguous, "coverage_conflict": conflict, "coverage_known": known,
        "expected_scanners": sorted(set(expected or [])), "missing_scanners": missing,
        "incomplete": incomplete, "complete": bool(completed) and known and not incomplete and not ambiguous,
        "coverage": "AMBIGUOUS" if ambiguous else "INCOMPLETE" if incomplete else "KNOWN" if known else "UNKNOWN",
        "finding_count": sum(row["finding_count"] for row in completed), "severity_summary": dict(severity),
        "scopes": {(row["scanner"], row["scope"]) for row in latest},
    }
