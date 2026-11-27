import hashlib
import json
import logging
import secrets
import uuid

from django.db import transaction
from django.db.models import Max
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from dojo.aspm_access.backend import managed_account
from dojo.aspm_ingestion.engagements import resolve_engagement
from dojo.aspm_ingestion.models import CommitScanSet, GeneratedReport, IngestionJob, IngestionToken, ScanRun
from dojo.aspm_ingestion.selection import SCAN_FIELDS, live_selection
from dojo.aspm_ingestion.storage import private_path, safe_name, save_original
from dojo.aspm_observability import metrics as telemetry
from dojo.scm.identity_v1 import repository_provider
from dojo.scm.models import Commit, Repository
from dojo.site_url import absolute_url

SCOPES = {"submit", "status", "read", "finalize", "reports", "engagement:select"}

logger = logging.getLogger(__name__)


class Conflict(APIException):
    status_code = 409
    default_detail = "The delivery key is already bound to a different request."


def issue_token(*, user, product, repository=None, scopes, expires_at, label):
    if user.is_superuser or user.is_staff or user.has_usable_password() or not user.is_active or managed_account(user):
        msg = "Use an active dedicated service account with an unusable password and no staff privileges."
        raise ValidationError(msg)
    if repository and repository.product_id != product.pk:
        msg = "Repository must belong to the token's Product."
        raise ValidationError(msg)
    if not set(scopes) <= SCOPES or expires_at <= timezone.now():
        msg = "Invalid scopes or expiry."
        raise ValidationError(msg)
    raw = secrets.token_urlsafe(40)
    token = IngestionToken.objects.create(
        user=user, product=product, repository=repository, scopes=sorted(set(scopes)),
        digest=hashlib.sha256(raw.encode()).hexdigest(), expires_at=expires_at, label=label,
    )
    return token, raw


def require_scope(token, scope):
    if not isinstance(token, IngestionToken) or scope not in token.scopes:
        msg = "A scoped ASPM service token is required."
        raise PermissionDenied(msg)


def token_repository(token, repository):
    if repository.product_id != token.product_id or (token.repository_id and token.repository_id != repository.pk):
        msg = "Repository is outside the token scope."
        raise PermissionDenied(msg)


def wake_dispatcher():
    from dojo.aspm_ingestion.tasks import dispatch_jobs  # noqa: PLC0415 -- task/service cycle

    try:
        dispatch_jobs.apply_async()
    except Exception:
        # The committed outbox is authoritative. Beat or the management command recovers this gap.
        logger.warning("ASPM outbox wake deferred; periodic dispatcher will recover pending jobs")


def accept_scan(token, data, upload, *, correlation_id=None):
    require_scope(token, "submit")
    if data["project_id"] != token.product_id:
        msg = "Product is outside the token scope."
        raise PermissionDenied(msg)
    repository = None
    if repository_id := data.get("repository_id"):
        repository = Repository.objects.filter(pk=repository_id, product_id=token.product_id).first()
        if repository is None:
            msg = "Repository is outside the token scope."
            raise PermissionDenied(msg)
        token_repository(token, repository)
        if data.get("repository_url") and repository.url != data["repository_url"]:
            raise ValidationError({"repository_url": "URL differs from repository_id."})
    elif token.repository_id:
        repository = token.repository
        if repository.url != data["repository_url"]:
            msg = "Repository is outside the token scope."
            raise PermissionDenied(msg)
    key, digest, size, storage_seconds = save_original(upload)
    retained = False
    try:
        metadata = {k: v for k, v in data.items() if k not in {"project_id", "repository_id", "repository_url", "commit_sha", "scanner_type", "idempotency_key", "sha256"}}
        url = repository.url if repository else data["repository_url"]
        identity = {"repository": url, "commit": data["commit_sha"], "scanner": data["scanner_type"], "metadata": metadata, "sha256": digest, "size": size}
        fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if data.get("sha256") and data["sha256"] != digest:
            raise ValidationError({"sha256": "The original does not match the supplied SHA256."})
        with transaction.atomic():
            repository, _ = Repository.objects.get_or_create(product_id=token.product_id, url=url, defaults={"provider": repository_provider(url)})
            token_repository(token, repository)
            commit, _ = Commit.objects.get_or_create(repository=repository, sha=data["commit_sha"], defaults={"branch": metadata.get("branch", "")})
            # Serialize only registration/finalization, after the file has been saved.
            Commit.objects.select_for_update().get(pk=commit.pk)
            scan, created = ScanRun.objects.get_or_create(
                product_id=token.product_id, delivery_key=data["idempotency_key"],
                defaults={"commit": commit, "engagement": lambda: resolve_engagement(token, commit, metadata), "submitted_by": token.user, "fingerprint": fingerprint,
                          "scanner": data["scanner_type"], "metadata": {**metadata, "correlation_id": correlation_id or uuid.uuid4().hex}, "artifact_path": key,
                          "artifact_sha256": digest, "artifact_size": size, "original_name": safe_name(upload.name),
                          "timings": {"artifact_storage_seconds": storage_seconds}},
            )
            if not created:
                if scan.fingerprint != fingerprint or scan.submitted_by_id != token.user_id:
                    raise Conflict
                if telemetry.ENABLED:
                    transaction.on_commit(lambda: telemetry.scan_event(scan.scanner, "duplicate"))
                return scan, False
            IngestionJob.objects.create(scan=scan, next_dispatch_at=timezone.now())
            if telemetry.ENABLED:
                def record_acceptance():
                    telemetry.scan_event(scan.scanner, "accepted")
                    telemetry.ARTIFACT_SIZE.labels("scan").observe(size)

                transaction.on_commit(record_acceptance)
            transaction.on_commit(wake_dispatcher)
        retained = True
        return scan, True
    finally:
        if not retained:
            private_path(key).unlink(missing_ok=True)


@transaction.atomic
def finalize_commit(commit, expected_scanners, *, scan_ids=None):
    Commit.objects.select_for_update().get(pk=commit.pk)
    scans = commit.scan_runs.order_by("created_at", "pk")
    if scan_ids is not None:
        selected = {str(identifier) for identifier in scan_ids}
        scans = scans.filter(pk__in=selected)
        if scans.count() != len(selected):
            msg = "All selected ScanRuns must belong to this commit."
            raise ValidationError(msg)
    identifiers = [str(pk) for pk in scans.values_list("pk", flat=True)[:1001]]
    if len(identifiers) > 1000:
        msg = "Select at most 1000 ScanRuns explicitly."
        raise ValidationError(msg)
    return CommitScanSet.objects.create(
        commit=commit, expected_scanners=sorted(set(expected_scanners)),
        scan_ids=identifiers,
    )


@transaction.atomic
def request_report(commit, scan_set_id=None, *, scan_ids=None, pipeline=None, expected_scanners=None):
    Commit.objects.select_for_update().get(pk=commit.pk)
    if scan_set_id is not None:
        if scan_ids is not None or pipeline is not None or expected_scanners is not None:
            msg = "scan_set_id cannot be combined with live selection options."
            raise ValidationError(msg)
        scan_set = commit.scan_sets.filter(pk=scan_set_id).first()
        if scan_set is None:
            msg = "Unknown scan_set_id for this commit."
            raise ValidationError(msg)
        scans = list(ScanRun.objects.filter(pk__in=scan_set.scan_ids).order_by("created_at", "pk").values(*SCAN_FIELDS))
        coverage_known = bool(scan_set.expected_scanners)
        selection_metadata = {"policy": "legacy-explicit-set", "coverage_known": coverage_known}
    else:
        selection = live_selection(commit, pipeline=pipeline, scan_ids=scan_ids, expected_scanners=expected_scanners)
        if selection["ambiguous"]:
            msg = "Multiple pipelines are available; choose pipeline or scan_ids."
            raise Conflict(msg)
        if not selection["scans"]:
            msg = "No COMPLETED ScanRuns are available in this selection."
            raise ValidationError(msg)
        scans = [{key: row[key] for key in SCAN_FIELDS} for row in selection["scans"]]
        scan_set = CommitScanSet.objects.create(
            commit=commit, scan_ids=[str(row["id"]) for row in scans],
            expected_scanners=selection["expected_scanners"],
        )
        coverage_known = selection["coverage_known"]
        selection_metadata = {"policy": "live-v1", "mode": "explicit_ids" if scan_ids is not None else "live", "pipeline": selection["pipeline"],
                              "coverage_known": coverage_known, "coverage": selection["coverage"],
                              "incomplete": selection["incomplete"],
                              "latest_runs": [{"id": str(row["id"]), "status": row["status"], "scanner": row["scanner"],
                                               "metadata": row["metadata"]} for row in selection["latest"]]}
    # This immutable manifest is the only source used by the asynchronous generator.
    for scan in scans:
        scan["id"] = str(scan["id"])
        for field in ("created_at", "finished_at"):
            scan[field] = scan[field].isoformat() if scan[field] else None
        scan["original_url"] = absolute_url(reverse("aspm_v1:artifact", args=[scan["id"]]))
    completed_scanners = {scan["scanner"] for scan in scans if scan["status"] == ScanRun.Status.COMPLETED}
    missing = sorted(set(scan_set.expected_scanners) - completed_scanners)
    complete = bool(scans) and coverage_known and not missing and not selection_metadata.get("incomplete", False) and all(scan["status"] == ScanRun.Status.COMPLETED for scan in scans)
    version = (commit.aspm_reports.aggregate(value=Max("version"))["value"] or 0) + 1
    report = GeneratedReport.objects.create(
        commit=commit, scan_set=scan_set, version=version,
        manifest={"schema_version": "1.0", "project": {"id": commit.repository.product_id, "name": commit.repository.product.name},
                  "repository": {"id": commit.repository_id, "url": commit.repository.url}, "commit_sha": commit.sha,
                  "commit_id": commit.pk, "branch": commit.branch, "parent_shas": commit.parent_shas,
                  "scan_set_id": str(scan_set.pk), "finalized_at": scan_set.created_at.isoformat(),
                  "expected_scanners": scan_set.expected_scanners, "missing_scanners": missing,
                  "complete": complete, "selection": selection_metadata, "scans": scans, "version": version,
                  "previous_report_ids": [str(pk) for pk in commit.aspm_reports.order_by("-version").values_list("pk", flat=True)[:20]]},
    )
    IngestionJob.objects.create(report=report, next_dispatch_at=timezone.now())
    transaction.on_commit(wake_dispatcher)
    if telemetry.ENABLED:
        transaction.on_commit(lambda: telemetry.report_event("requested"))
    return report


def retry_scan(scan):
    # Import is fenced by a session advisory lock in the worker. Only terminal failures can retry.
    with transaction.atomic():
        scan = ScanRun.objects.select_for_update().get(pk=scan.pk)
        if scan.status != ScanRun.Status.FAILED:
            msg = "Only a failed ScanRun can be retried."
            raise Conflict(msg)
        scan.status = ScanRun.Status.ACCEPTED
        scan.error_code = ""
        scan.recovery_count = 0
        scan.save(update_fields=["status", "error_code", "recovery_count"])
        IngestionJob.objects.update_or_create(scan=scan, defaults={"next_dispatch_at": timezone.now()})
        transaction.on_commit(wake_dispatcher)
    if telemetry.ENABLED:
        transaction.on_commit(lambda: telemetry.scan_event(scan.scanner, "retry"))
    return scan
