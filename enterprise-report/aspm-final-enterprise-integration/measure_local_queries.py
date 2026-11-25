"""Measure scoped workspace SQL against the disposable Django runtime."""
# ruff: noqa: INP001, T201
import json
import statistics
import time
from uuid import UUID

from django.conf import settings
from django.db import connection, transaction
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from dojo.aspm_access.backend import BACKEND
from dojo.aspm_access.middleware import SESSION_KEY
from dojo.aspm_access.models import SsoIdentity, SsoProductGrant
from dojo.aspm_ingestion.models import ScanRun
from dojo.scm.models import Commit

if connection.settings_dict["NAME"] != "aspm_final_integration":
    msg = "Expected the isolated local qualification database."
    raise RuntimeError(msg)

identity = SsoIdentity.objects.filter(issuer=settings.ASPM_OIDC_ISSUER).first()
grant = SsoProductGrant.objects.get(product__name="TEST")
example = ScanRun.objects.filter(product=grant.product).select_related("commit").first()
sample = []


def measure(client, role, label, url):
    runs = []
    for _ in range(3):
        with CaptureQueriesContext(connection) as capture:
            started = time.perf_counter()
            response = client.get(url, secure=True)
            elapsed = (time.perf_counter() - started) * 1000
        if response.status_code != 200:
            msg = f"{role} {label} returned {response.status_code}"
            raise RuntimeError(msg)
        runs.append({"queries": len(capture), "elapsed_ms": round(elapsed, 1)})
    sample.append({
        "role": role, "page": label, "queries": [run["queries"] for run in runs],
        "median_ms": statistics.median(run["elapsed_ms"] for run in runs),
    })


for role in ("user", "expert", "secops"):
    client = Client(HTTP_HOST="localhost:48141")
    client.force_login(identity.user, backend=BACKEND)
    session = client.session
    now = int(time.time())
    session[SESSION_KEY] = {"issuer": identity.issuer, "role": role, "groups": [str(grant.group_id)], "checked": now, "expires": now + 120}
    session.save()
    measure(client, role, "Projects", reverse("aspm_projects"))
    measure(client, role, "Reports", reverse("aspm_reports"))
    if role in {"expert", "secops"}:
        measure(client, role, "Findings", reverse("all_findings"))
    if role == "secops":
        measure(client, role, "Settings", reverse("system_settings"))
        measure(client, role, "Engagement policy", reverse("aspm_engagement_policy", args=(grant.product_id,)))
        measure(client, role, "Webhooks", reverse("aspm_webhooks"))
    with transaction.atomic():
        for count, char in ((1, "8"), (100, "9"), (1000, "0")):
            commit = Commit.objects.create(repository_id=example.commit.repository_id, sha=char * 40)
            ScanRun.objects.bulk_create([
                ScanRun(
                    commit=commit, product_id=example.product_id, submitted_by_id=example.submitted_by_id,
                    delivery_key=f"qual-query-{char}-{index}", fingerprint=example.fingerprint, scanner=example.scanner,
                    artifact_path=example.artifact_path, artifact_sha256=example.artifact_sha256,
                    artifact_size=example.artifact_size, original_name=example.original_name,
                    metadata={"pipeline_id": "overview", "scan_scope": f"scope-{index}"},
                )
                for index in range(count)
            ])
            measure(client, role, f"Commit Overview, {count} accepted ScanRun(s)", reverse("aspm_commit_evidence", args=(commit.pk,)))
        transaction.set_rollback(True)

with transaction.atomic():
    other = SsoProductGrant.objects.get(product__name="PAYMENTS")
    groups = [UUID(int=2**96 + index) for index in range(10_000)]
    SsoProductGrant.objects.bulk_create([
        SsoProductGrant(issuer=identity.issuer, group_id=group, product_id=grant.product_id if index < 256 else other.product_id)
        for index, group in enumerate(groups)
    ], batch_size=1000)
    session = client.session
    now = int(time.time())
    session[SESSION_KEY] = {"issuer": identity.issuer, "role": "user", "groups": [str(group) for group in groups[:256]], "checked": now, "expires": now + 120}
    session.save()
    response = client.get(reverse("aspm_projects"), secure=True)
    if b">TEST</a>" not in response.content or b">PAYMENTS</a>" in response.content:
        msg = "High-cardinality grant isolation did not hold."
        raise RuntimeError(msg)
    measure(client, "user", "Projects, 10,000 grant mappings and 256 asserted entitlements", reverse("aspm_projects"))
    transaction.set_rollback(True)

print(json.dumps(sample, indent=2))
