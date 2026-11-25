"""Export the immutable file references from a designated local hardening database."""
import json
import os

from django.db import connection

from dojo.aspm_ingestion.models import GeneratedReport, ScanRun


def manifest():
    expected = os.environ["ASPM_QUALIFICATION_DB"]
    if not expected.startswith("aspm_hardening") or connection.settings_dict["NAME"] != expected:
        raise RuntimeError("Expected an explicitly named isolated hardening lab database")
    entries = []
    for path, sha256 in ScanRun.objects.order_by("artifact_path").values_list("artifact_path", "artifact_sha256").iterator():
        if path and sha256:
            entries.append((path, sha256))
    for html, json_path, sums in GeneratedReport.objects.filter(status="COMPLETED").values_list("html_path", "json_path", "checksums").iterator():
        entries.extend([(html, sums["html"]), (json_path, sums["json"])])
    return sorted(entries)


if __name__ == "__main__":
    print(json.dumps(manifest()))
