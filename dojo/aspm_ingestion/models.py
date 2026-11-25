import uuid

from django.conf import settings
from django.db import models


class IngestionToken(models.Model):

    """Only a digest is stored; a dedicated unprivileged service user owns deliveries."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    product = models.ForeignKey("dojo.Product", on_delete=models.PROTECT)
    repository = models.ForeignKey("dojo.Repository", null=True, blank=True, on_delete=models.PROTECT)
    digest = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=120)
    scopes = models.JSONField(default=list)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class IngestionRateWindow(models.Model):
    token = models.OneToOneField(IngestionToken, primary_key=True, on_delete=models.CASCADE)
    bucket_minute = models.BigIntegerField()
    requests = models.IntegerField()

    class Meta:
        db_table = "aspm_ingestion_rate"


class EngagementStrategy(models.TextChoices):
    DEFAULT = "default", "Default"
    REPOSITORY = "repository", "Repository"
    BRANCH = "branch", "Branch"
    ENVIRONMENT = "environment", "Environment"
    EXPLICIT = "explicit", "Explicit"


class EngagementPolicy(models.Model):
    product = models.ForeignKey("dojo.Product", on_delete=models.CASCADE)
    repository = models.ForeignKey("dojo.Repository", null=True, blank=True, on_delete=models.CASCADE)
    strategy = models.CharField(max_length=16, choices=EngagementStrategy, default=EngagementStrategy.DEFAULT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("product",), condition=models.Q(repository__isnull=True), name="aspm_product_engagement_policy"),
            models.UniqueConstraint(fields=("repository",), condition=models.Q(repository__isnull=False), name="aspm_repo_engagement_policy"),
        ]
        permissions = [("manage_engagement_policy", "Can manage ASPM engagement policies")]


class ManagedEngagement(models.Model):
    repository = models.ForeignKey("dojo.Repository", on_delete=models.PROTECT)
    strategy = models.CharField(max_length=16, choices=EngagementStrategy)
    scope = models.CharField(max_length=150, blank=True)
    engagement = models.OneToOneField("dojo.Engagement", on_delete=models.PROTECT)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("repository", "strategy", "scope"), condition=models.Q(archived_at__isnull=True), name="aspm_active_engagement_scope"),
        ]


class ScanRun(models.Model):
    class Status(models.TextChoices):
        ACCEPTED = "ACCEPTED"
        PROCESSING = "PROCESSING"
        COMPLETED = "COMPLETED"
        FAILED = "FAILED"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey("dojo.Product", on_delete=models.PROTECT)
    commit = models.ForeignKey("dojo.Commit", related_name="scan_runs", on_delete=models.PROTECT)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    delivery_key = models.CharField(max_length=200)
    fingerprint = models.CharField(max_length=64)
    scanner = models.CharField(max_length=200)
    metadata = models.JSONField(default=dict)
    artifact_path = models.CharField(max_length=300)
    artifact_sha256 = models.CharField(max_length=64)
    artifact_size = models.PositiveBigIntegerField()
    original_name = models.CharField(max_length=200)
    status = models.CharField(max_length=16, choices=Status, default=Status.ACCEPTED)
    engagement = models.ForeignKey("dojo.Engagement", null=True, blank=True, on_delete=models.PROTECT)
    test = models.OneToOneField("dojo.Test", null=True, blank=True, on_delete=models.PROTECT)
    attempt = models.PositiveIntegerField(default=0)
    recovery_count = models.PositiveIntegerField(default=0)
    observation_generation = models.PositiveIntegerField(default=0)
    finding_count = models.PositiveBigIntegerField(default=0)
    severity_summary = models.JSONField(default=dict)
    timings = models.JSONField(default=dict)
    error_code = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("product", "delivery_key"), name="aspm_delivery_unique")]
        indexes = [models.Index(fields=("commit", "status", "created_at"), name="aspm_scan_commit_status")]


class FindingObservation(models.Model):

    """Values, not a live FK to Finding: deleting/editing a Finding cannot rewrite history."""

    scan = models.ForeignKey(ScanRun, related_name="observations", on_delete=models.PROTECT)
    generation = models.PositiveIntegerField()
    source_finding_id = models.BigIntegerField()
    identity = models.CharField(max_length=64, db_index=True)
    severity = models.CharField(max_length=20)
    snapshot = models.JSONField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=("scan", "generation", "source_finding_id"), name="aspm_observation_unique")]


class CommitScanSet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    commit = models.ForeignKey("dojo.Commit", related_name="scan_sets", on_delete=models.PROTECT)
    scan_ids = models.JSONField()
    expected_scanners = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)


class CommitScanSetMembership(models.Model):

    """FK-backed mirror of the frozen UUID list, maintained and protected by PostgreSQL."""

    scan_set = models.ForeignKey("dojo.CommitScanSet", related_name="memberships", on_delete=models.PROTECT)
    scan = models.ForeignKey("dojo.ScanRun", on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("scan_set", "scan"), name="aspm_finalized_scan_unique")]


class GeneratedReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    commit = models.ForeignKey("dojo.Commit", related_name="aspm_reports", on_delete=models.PROTECT)
    scan_set = models.ForeignKey(CommitScanSet, on_delete=models.PROTECT)
    version = models.PositiveIntegerField()
    manifest = models.JSONField()
    status = models.CharField(max_length=16, choices=ScanRun.Status, default=ScanRun.Status.ACCEPTED)
    json_path = models.CharField(max_length=300, blank=True)
    html_path = models.CharField(max_length=300, blank=True)
    checksums = models.JSONField(default=dict)
    timings = models.JSONField(default=dict)
    error_code = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("commit", "version"), name="aspm_report_version_unique")]


class IngestionJob(models.Model):

    """Transactional outbox retained until the work actually finishes, not just broker ACK."""

    scan = models.OneToOneField(ScanRun, null=True, on_delete=models.CASCADE)
    report = models.OneToOneField(GeneratedReport, null=True, on_delete=models.CASCADE)
    next_dispatch_at = models.DateTimeField(db_index=True)
    deliveries = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.CheckConstraint(condition=(models.Q(scan__isnull=False, report__isnull=True) | models.Q(scan__isnull=True, report__isnull=False)), name="aspm_job_one_target")]
