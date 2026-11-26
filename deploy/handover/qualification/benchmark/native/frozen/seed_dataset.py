# Standalone trusted-lab CLI: assertions validate results; progress/PATH tools are intentional.
# ruff: noqa: INP001, PERF401, PT018, S101, T201
"""Run only in the fresh acceptance seed. Bulk seed is never the measured import."""

import base64
import json
import secrets
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from django.contrib.sessions.backends.db import SessionStore
from django.db import connection
from django.db.models import Count
from rest_framework.authtoken.models import Token

from dojo.authorization.roles_permissions import Roles
from dojo.models import (
    BurpRawRequestResponse,
    Development_Environment,
    Dojo_User,
    Engagement,
    Finding,
    Notes,
    Product,
    Product_Member,
    Product_Type,
    Role,
    System_Settings,
    Test,
    Test_Type,
)
from dojo.url.models import URL
from dojo.vulnerability.models import FindingVulnerabilityReference, Vulnerability

assert connection.settings_dict["HOST"] == "postgres"
assert connection.settings_dict["NAME"] == "aspm_acceptance_seed"
assert Finding.objects.count() == Test.objects.count() == Engagement.objects.count() == Product.objects.count() == 0
start = time.time()
origin = datetime(2026, 7, 1, 12, tzinfo=UTC)
settings = System_Settings.objects.get(no_cache=True)
settings.enable_deduplication = True
settings.save(update_fields=["enable_deduplication"])
admin = Dojo_User.objects.create_superuser(
    "acceptance_operator",
    email="operator@acceptance.invalid",
    password=secrets.token_urlsafe(32),
)
prod_type = Product_Type.objects.create(
    name="Acceptance fixture",
    description="Synthetic deterministic fixture; not production data",
)
scan, _ = Test_Type.objects.get_or_create(name="ZAP Scan")
environment, _ = Development_Environment.objects.get_or_create(name="Acceptance isolated")
products = [
    Product(id=i + 1, name="Project " + letter, description="Acceptance project " + letter, prod_type=prod_type)
    for i, letter in enumerate("AB")
]
Product.objects.bulk_create(products)
engagements = []
for product in products:
    for index in range(5):
        engagements.append(
            Engagement(
                id=(product.pk - 1) * 5 + index + 1,
                product=product,
                name=f"{product.name[-1]}{index + 1}",
                target_start=origin.date(),
                target_end=date(2026, 11, 1),
                deduplication_on_engagement=False,
            ),
        )
Engagement.objects.bulk_create(engagements)
tests = []
for engagement in engagements:
    for index in range(250):
        tests.append(
            Test(
                id=(engagement.pk - 1) * 250 + index + 1,
                engagement=engagement,
                test_type=scan,
                scan_type="ZAP Scan",
                environment=environment,
                title=f"{engagement.name} Test {index + 1:03}",
                target_start=origin,
                target_end=datetime(2026, 11, 1, tzinfo=UTC),
                percent_complete=100,
            ),
        )
Test.objects.bulk_create(tests, batch_size=500)
accounts = []
for index in range(10):
    password = secrets.token_urlsafe(24)
    user = Dojo_User.objects.create_user(
        f"acceptance_vu_{index + 1:02}",
        password=password,
        email=f"vu{index + 1}@acceptance.invalid",
        is_staff=False,
        is_superuser=False,
    )
    memberships = [1] if index < 4 else [2] if index < 8 else [1, 2]
    role = Role.objects.get(pk=Roles.Maintainer if index < 8 else Roles.Owner)
    for product_id in memberships:
        products[product_id - 1].authorized_users.add(user)
        Product_Member.objects.get_or_create(product_id=product_id, user=user, defaults={"role": role})
    token = Token.objects.create(user=user)
    session = SessionStore()
    session["_auth_user_id"] = str(user.pk)
    session["_auth_user_backend"] = "django.contrib.auth.backends.ModelBackend"
    session["_auth_user_hash"] = user.get_session_auth_hash()
    session.set_expiry(datetime(2030, 1, 1, tzinfo=UTC))
    session.save()
    accounts.append(
        {
            "vu": index,
            "username": user.username,
            "user_id": user.pk,
            "password": password,
            "token": token.key,
            "session": session.session_key,
            "products": memberships,
            "role_id": role.pk,
            "is_staff": False,
            "is_superuser": False,
        },
    )
private = Path("/acceptance-telemetry/accounts.json")
private.write_text(json.dumps(accounts, indent=2) + "\n", encoding="utf-8")
private.chmod(0o600)

severities = ["Critical", "High", "Medium", "Low", "Info"]
for test in tests:
    findings = []
    for offset in range(400):
        ident = (test.pk - 1) * 400 + offset + 1
        day = origin.date() + timedelta(days=(test.pk * 7 + offset) % 120)
        closed = (offset // 5) % 5 == 1
        finding = Finding(
            id=ident,
            test=test,
            reporter=admin,
            title=f"Acceptance seed {ident:07} {severities[offset % 5]}",
            date=day,
            sla_start_date=day,
            severity=severities[offset % 5],
            numerical_severity=Finding.get_numerical_severity(severities[offset % 5]),
            cwe=[79, 89, 22, 200, 352][offset % 5],
            active=not closed,
            is_mitigated=closed,
            mitigated=datetime.combine(day + timedelta(days=3), datetime.min.time(), UTC) if closed else None,
            verified=offset % 7 != 0,
            duplicate=False,
            false_p=False,
            out_of_scope=False,
            dynamic_finding=True,
            static_finding=False,
            description=f"Deterministic finding {ident}. Synthetic request validation weakness in service {test.pk}. "
            "The fixture represents an independently observed occurrence, with explicit scope, impact and evidence. "
            * 2,
            mitigation="Validate and normalize input; apply parameterized queries and least privilege.",
            impact="A synthetic unauthorized operation may disclose representative non-sensitive data.",
            references="https://acceptance.invalid/security/reference",
            scanner_confidence=4,
            vuln_id_from_tool=f"seed-{ident:07}",
        )
        finding.hash_code = finding.compute_hash_code()
        findings.append(finding)
    Finding.objects.bulk_create(findings, batch_size=400)
    if test.pk % 100 == 0:
        print("SEEDED", test.pk * 400, "elapsed", round(time.time() - start, 1), flush=True)

# Representative auxiliary relations, deterministic IDs; no external endpoints.
vulnerabilities = [
    Vulnerability(vulnerability_id=f"CVE-2026-{99000 + i}", vulnerability_id_type="CVE") for i in range(20)
]
Vulnerability.objects.bulk_create(vulnerabilities)
references = []
evidence = []
notes = []
for test in tests:
    first = (test.pk - 1) * 400 + 1
    for offset in range(4):
        references.append(
            FindingVulnerabilityReference(
                finding_id=first + offset,
                vulnerability=vulnerabilities[(test.pk + offset) % 20],
                order=0,
            ),
        )
    for offset in range(2):
        evidence.append(
            BurpRawRequestResponse(
                finding_id=first + offset,
                burpRequestBase64=base64.b64encode(b"GET /synthetic HTTP/1.1\r\nHost: acceptance.invalid\r\n\r\n"),
                burpResponseBase64=base64.b64encode(
                    b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nSynthetic evidence",
                ),
            ),
        )
    notes.append(
        Notes(
            entry=f"Acceptance evidence note for Test {test.pk}; intentionally fabricated.",
            author=admin,
            date=origin,
        ),
    )
FindingVulnerabilityReference.objects.bulk_create(references, batch_size=1000)
BurpRawRequestResponse.objects.bulk_create(evidence, batch_size=1000)
Notes.objects.bulk_create(notes, batch_size=1000)
through = Finding.notes.through
through.objects.bulk_create(
    [through(finding_id=(test.pk - 1) * 400 + 1, notes_id=note.pk) for test, note in zip(tests, notes, strict=True)],
    batch_size=1000,
)
for test in tests:
    location = URL.get_or_create_from_values(
        protocol="https",
        host=f"test-{test.pk}.acceptance.invalid",
        path="service",
    ).location
    location.associate_with_finding(Finding.objects.get(pk=(test.pk - 1) * 400 + 1), audit_time=origin)

# Make auto_now fields reproducible after bulk insertion; this is seed-only SQL.
with connection.cursor() as cursor:
    cursor.execute(
        "UPDATE dojo_finding SET created=(date + time '12:00') AT TIME ZONE 'UTC', updated=((date + time '12:00') AT TIME ZONE 'UTC') + interval '1 day', last_status_update=((date + time '12:00') AT TIME ZONE 'UTC') + interval '1 day'",
    )
    cursor.execute("UPDATE dojo_test SET created=target_start, updated=target_end")
    for table in ["dojo_product", "dojo_engagement", "dojo_test", "dojo_finding"]:
        cursor.execute(
            "SELECT setval(pg_get_serial_sequence(%s,'id'),(SELECT max(id) FROM " + table + "),true)",
            [table],
        )
    cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")
    cursor.execute("ANALYZE")

counts = list(Finding.objects.order_by().values("test_id").annotate(n=Count("pk")).values_list("n", flat=True))
assert len(counts) == 2500 and min(counts) == max(counts) == 400
assert Product.objects.count() == 2 and Engagement.objects.count() == 10 and Test.objects.count() == 2500
assert Finding.objects.count() == 1000000 and not Finding.objects.filter(duplicate=True).exists()
manifest = {
    "seed": 35100101,
    "products": 2,
    "engagements": 10,
    "tests": 2500,
    "findings": 1000000,
    "findings_per_test": 400,
    "deduplication_enabled": True,
    "cve_references": len(references),
    "evidence_rows": len(evidence),
    "notes": len(notes),
    "location_references": 2500,
    "bulk_seed_only": True,
    "measured_import_uses_native_api": True,
    "elapsed_s": time.time() - start,
}
Path("/acceptance-telemetry/seed-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("SEED_COMPLETE", json.dumps(manifest), flush=True)
