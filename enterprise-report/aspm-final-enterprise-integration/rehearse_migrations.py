"""Validate upgrade and schema rollback against an isolated legacy evidence row."""
# ruff: noqa: INP001, T201 -- standalone lab script prints a verification record
import json

from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

if connection.settings_dict["NAME"] != "aspm_final_upgrade":
    msg = "Expected the empty, isolated aspm_final_upgrade database."
    raise RuntimeError(msg)

base = ("dojo", "0319_aspm_webhook_dispatch_lease")
candidate = ("dojo", "0321_aspm_sso_identity")
call_command("migrate", *base, interactive=False, verbosity=0)
old = MigrationExecutor(connection).loader.project_state([base]).apps
ptype = old.get_model("dojo", "Product_Type").objects.create(name="Migration qualification")
product = old.get_model("dojo", "Product").objects.create(name="Upgrade sample", description="Local fixture", prod_type=ptype)
repo = old.get_model("dojo", "Repository").objects.create(product=product, url="https://git.example.test/qual")
commit = old.get_model("dojo", "Commit").objects.create(repository=repo, sha="a" * 40)
user = old.get_model(settings.AUTH_USER_MODEL).objects.create(username="upgrade-qualification")
today = timezone.localdate()
engagement = old.get_model("dojo", "Engagement").objects.create(
    product=product, commit=commit, name="Legacy CI engagement", target_start=today, target_end=today,
)
ttype = old.get_model("dojo", "Test_Type").objects.create(name="Upgrade scanner")
now = timezone.now()
test = old.get_model("dojo", "Test").objects.create(engagement=engagement, test_type=ttype, target_start=now, target_end=now)
scan_type = old.get_model("dojo", "ScanRun")
scan = scan_type.objects.create(
    product=product, commit=commit, submitted_by=user, test=test, status="PROCESSING",
    delivery_key="upgrade-fixture", fingerprint="b" * 64, scanner=ttype.name,
    artifact_path="test-fixture-only", artifact_sha256="a" * 64, artifact_size=1, original_name="fixture.json", attempt=1,
)
old.get_model("dojo", "FindingObservation").objects.create(
    scan=scan, generation=1, source_finding_id=1, identity="c" * 64, severity="High",
    snapshot={"title": "Historical migration fixture", "severity": "High"},
)
scan_type.objects.filter(pk=scan.pk).update(status="COMPLETED", observation_generation=1, finding_count=1)
call_command("migrate", *candidate, interactive=False, verbosity=0)
current = MigrationExecutor(connection).loader.project_state([candidate]).apps
upgraded = current.get_model("dojo", "ScanRun").objects.get(pk=scan.pk)
if (upgraded.test_id, upgraded.engagement_id, upgraded.status) != (test.pk, None, "COMPLETED"):
    msg = "Upgrade changed a pre-existing scan assignment or state."
    raise RuntimeError(msg)
if upgraded.observations.get().snapshot["title"] != "Historical migration fixture":
    msg = "Upgrade changed the historical observation."
    raise RuntimeError(msg)

call_command("migrate", *base, interactive=False, verbosity=0)
restored = scan_type.objects.get(pk=scan.pk)
if (restored.test_id, restored.status) != (test.pk, "COMPLETED"):
    msg = "Rollback changed a pre-existing scan assignment or state."
    raise RuntimeError(msg)
if restored.observations.get().snapshot["title"] != "Historical migration fixture":
    msg = "Rollback changed the historical observation."
    raise RuntimeError(msg)
print(json.dumps({"baseline": base[1], "upgraded": candidate[1], "preserved_legacy_evidence": True, "rollback_without_new_assignments": True}, indent=2))
