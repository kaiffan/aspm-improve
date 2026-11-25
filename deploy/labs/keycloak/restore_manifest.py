"""Hash relational and file evidence. Execute inside the dedicated lab's Django shell."""
# ruff: noqa: INP001, T201 -- standalone local qualification prints a hash-only JSON manifest
import hashlib
import json
from pathlib import Path

from django.conf import settings
from django.db import connection

from dojo.aspm_access.models import SsoIdentity, SsoProductGrant
from dojo.aspm_ingestion.models import EngagementPolicy, FindingObservation, GeneratedReport, ManagedEngagement, ScanRun
from dojo.finding.models import Finding

if connection.settings_dict["NAME"] not in {"aspm_final_integration", "aspm_final_restore"}:
    msg = "Use the dedicated lab or restore database."
    raise RuntimeError(msg)

checks = [
    (EngagementPolicy, ("id", "product_id", "repository_id", "strategy")),
    (ManagedEngagement, ("id", "repository_id", "strategy", "scope", "engagement_id", "archived_at")),
    (ScanRun, ("id", "product_id", "commit_id", "test_id", "engagement_id", "status", "artifact_path", "artifact_sha256")),
    (Finding, ("id", "test_id", "false_p", "hash_code")),
    (FindingObservation, ("id", "scan_id", "generation", "identity", "snapshot")),
    (GeneratedReport, ("id", "commit_id", "version", "manifest", "checksums")),
    (SsoIdentity, ("id", "issuer", "subject", "user_id")),
    (SsoProductGrant, ("id", "issuer", "group_id", "product_id")),
]

results = {}
for model, fields in checks:
    digest = hashlib.sha256()
    count = 0
    for record in model.objects.order_by("pk").values_list(*fields).iterator():
        digest.update(json.dumps(record, sort_keys=True, default=str).encode() + b"\n")
        count += 1
    results[model.__name__] = {"rows": count, "sha256": digest.hexdigest()}

root = Path(settings.ASPM_ARTIFACT_ROOT)
files = [
    *ScanRun.objects.order_by("pk").values_list("artifact_path", "artifact_sha256"),
    *((report.html_path, report.checksums["html"]) for report in GeneratedReport.objects.filter(status="COMPLETED")),
    *((report.json_path, report.checksums["json"]) for report in GeneratedReport.objects.filter(status="COMPLETED")),
]
for name, expected in files:
    with (root / name).open("rb") as source:
        actual = hashlib.file_digest(source, "sha256").hexdigest()
    if actual != expected:
        msg = "Restored file content does not match its database checksum."
        raise RuntimeError(msg)
results["files_verified"] = len(files)

print(json.dumps(results, sort_keys=True, indent=2))
