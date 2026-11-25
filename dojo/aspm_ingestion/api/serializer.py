import json
import re
from urllib.parse import urlsplit

from rest_framework import serializers

from dojo.aspm_ingestion.models import CommitScanSet, GeneratedReport, ScanRun
from dojo.scm.identity_v1 import canonical_repository_url, canonical_sha
from dojo.tools.factory import PARSERS, get_parser


class ScanUploadSerializer(serializers.Serializer):
    project_id = serializers.IntegerField(min_value=1)
    repository_id = serializers.IntegerField(min_value=1, required=False)
    repository_url = serializers.CharField(max_length=600, required=False)
    commit_sha = serializers.CharField(max_length=64)
    scanner_type = serializers.CharField(max_length=200)
    idempotency_key = serializers.RegexField(r"^[A-Za-z0-9._:/@+-]{1,200}$", required=False, help_text="Required either here or in the Idempotency-Key header.")
    file = serializers.FileField(write_only=True, allow_empty_file=False)
    sha256 = serializers.RegexField(r"^[a-f0-9]{64}$", required=False)
    branch = serializers.CharField(max_length=150, required=False)
    environment = serializers.CharField(max_length=150, required=False)
    engagement_id = serializers.IntegerField(min_value=1, max_value=2**63 - 1, required=False)
    build_id = serializers.CharField(max_length=150, required=False)
    pipeline_id = serializers.CharField(max_length=150, required=False)
    job_id = serializers.CharField(max_length=150, required=False)
    attempt_number = serializers.IntegerField(min_value=1, max_value=1000000, required=False)
    scanner_version = serializers.CharField(max_length=100, required=False)
    scan_started = serializers.DateTimeField(required=False)
    scan_finished = serializers.DateTimeField(required=False)
    expected_scanners = serializers.JSONField(required=False, help_text="Optional JSON array of expected scanner types for this pipeline. Omission means unknown coverage.")
    scan_scope = serializers.CharField(max_length=200, required=False)
    pipeline_url = serializers.URLField(max_length=1000, required=False)

    def to_internal_value(self, data):
        if unknown := set(data) - set(self.fields):
            raise serializers.ValidationError(dict.fromkeys(sorted(unknown), "Unknown field."))
        return super().to_internal_value(data)

    def validate_repository_url(self, value):
        try:
            return canonical_repository_url(value)
        except ValueError as error:
            msg = "Supply a repository HTTP(S) URL without credentials, query or fragment."
            raise serializers.ValidationError(msg) from error

    def validate_commit_sha(self, value):
        try:
            return canonical_sha(value)
        except ValueError as error:
            msg = "Supply a full 40 or 64 character Git SHA."
            raise serializers.ValidationError(msg) from error

    def validate_scanner_type(self, value):
        if value not in PARSERS or not hasattr(PARSERS[value], "get_findings"):
            msg = "Select an installed file-based DefectDojo parser."
            raise serializers.ValidationError(msg)
        try:
            get_parser(value)
        except ValueError as error:
            msg = "This DefectDojo parser is disabled."
            raise serializers.ValidationError(msg) from error
        return value

    def validate_expected_scanners(self, value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError as error:
                msg = "Use a JSON array of expected scanner types."
                raise serializers.ValidationError(msg) from error
        if not isinstance(value, list) or not 1 <= len(value) <= 100 or any(not isinstance(item, str) or item not in PARSERS for item in value):
            msg = "Provide 1 to 100 installed scanner types."
            raise serializers.ValidationError(msg)
        return sorted(set(value))

    def validate_pipeline_url(self, value):
        parts = urlsplit(value)
        if parts.scheme != "https" or parts.username or parts.password or parts.query or parts.fragment:
            msg = "Use HTTPS without credentials, query or fragment."
            raise serializers.ValidationError(msg)
        return value

    def validate(self, attrs):
        if not attrs.get("idempotency_key"):
            msg = "Provide idempotency_key or the Idempotency-Key header."
            raise serializers.ValidationError(msg)
        if not attrs.get("repository_id") and not attrs.get("repository_url"):
            msg = "repository_id or repository_url is required."
            raise serializers.ValidationError(msg)
        if attrs.get("scan_started") and attrs.get("scan_finished") and attrs["scan_finished"] < attrs["scan_started"]:
            msg = "scan_finished must not precede scan_started."
            raise serializers.ValidationError(msg)
        for key, value in list(attrs.items()):
            if isinstance(value, str) and re.search(r"[\x00-\x1f\x7f]", value):
                raise serializers.ValidationError({key: "Control characters are not allowed."})
            if key in {"scan_started", "scan_finished"}:
                attrs[key] = value.isoformat()
        return attrs


class ScanRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanRun
        fields = ("id", "product", "commit", "scanner", "metadata", "status", "artifact_sha256", "artifact_size", "original_name", "test", "attempt", "finding_count", "severity_summary", "timings", "error_code", "created_at", "started_at", "finished_at")
        read_only_fields = fields


class FinalizeSerializer(serializers.Serializer):
    expected_scanners = serializers.ListField(child=serializers.CharField(max_length=200), min_length=1, max_length=100)
    scan_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=1000, required=False, help_text="Pin this pipeline's deliveries. If omitted, include all accepted runs currently on the commit.")

    def validate_expected_scanners(self, value):
        if any(scanner not in PARSERS for scanner in value):
            msg = "All expected scanners must be installed DefectDojo scan types."
            raise serializers.ValidationError(msg)
        return value


class ScanSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommitScanSet
        fields = ("id", "commit", "scan_ids", "expected_scanners", "created_at")
        read_only_fields = fields


class ReportRequestSerializer(serializers.Serializer):
    scan_set_id = serializers.UUIDField(required=False, help_text="Optional legacy immutable set. No finalize is required.")
    pipeline = serializers.CharField(max_length=200, required=False, help_text="Context from the commit UI, e.g. pipeline:123.")
    scan_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=1000, required=False)
    expected_scanners = serializers.ListField(child=serializers.CharField(max_length=200), min_length=1, max_length=100, required=False)

    validate_expected_scanners = FinalizeSerializer.validate_expected_scanners

    def validate(self, attrs):
        if "scan_set_id" in attrs and len(attrs) > 1:
            msg = "scan_set_id cannot be combined with live selection options."
            raise serializers.ValidationError(msg)
        if "pipeline" in attrs and "scan_ids" in attrs:
            msg = "Choose pipeline or scan_ids."
            raise serializers.ValidationError(msg)
        return attrs


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedReport
        fields = ("id", "commit", "version", "scan_set", "manifest", "status", "checksums", "timings", "error_code", "created_at")
        read_only_fields = fields
