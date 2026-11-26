import json
import secrets
import time
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token

from dojo.aspm_access.backend import BACKEND
from dojo.aspm_access.middleware import FLOW_KEY, SESSION_KEY
from dojo.aspm_access.models import SsoIdentity, SsoProductGrant
from dojo.aspm_ingestion.models import CommitScanSet, GeneratedReport, ScanRun
from dojo.models import Engagement, Finding, Test
from dojo.scm.models import Commit, Repository
from unittests.test_aspm_ingestion import IngestionFixture, generic

ISSUER = "https://idp.example.com/realms/qualification"
GROUP_TEST = UUID("30000000-0000-4000-8000-000000000001")
GROUP_PAYMENTS = UUID("30000000-0000-4000-8000-000000000002")


@override_settings(
    ASPM_OIDC_ENABLED=True, ASPM_OIDC_ISSUER=ISSUER, ASPM_OIDC_CLIENT_ID="aspm", ASPM_OIDC_CLIENT_SECRET=secrets.token_urlsafe(24),
    ASPM_OIDC_CALLBACK_URL="https://testserver/sso/callback", SITE_URL="https://testserver",
    SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True, ASPM_OIDC_GROUP_TTL=30,
)
class KeycloakProtocolTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.local = get_user_model().objects.create_superuser(username="existing-local", email="same@example.com")
        cls.signing_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(cls.signing_key.public_key()))
        cls.jwk.update(kid="test-rs256", alg="RS256", use="sig")

    def _begin(self, **params):
        response = self.client.get(reverse("aspm_oidc_login"), params, secure=True)
        self.assertEqual(response.status_code, 302)
        return parse_qs(urlsplit(response.url).query), self.client.session[FLOW_KEY]

    def _claims(self, flow):
        now = int(time.time())
        return {
            "iss": ISSUER, "sub": "subject", "aud": "aspm", "azp": "aspm", "exp": now + 360,
            "iat": now, "nonce": flow["nonce"], "email": "same@example.com", "aspm_roles": ["aspm-expert"],
        }

    def _callback(self, query, claims, key=None):
        token = jwt.encode(claims, key or self.signing_key, algorithm="RS256", headers={"kid": "test-rs256"})
        with patch("dojo.aspm_access.oidc._json_response", side_effect=[{"id_token": token}, {"keys": [self.jwk]}]) as exchange:
            response = self.client.get(reverse("aspm_oidc_callback"), {"state": query["state"][0], "code": "short-code"}, secure=True)
        return response, exchange

    def test_code_pkce_nonce_signature_session_rotation_and_local_identity(self):
        query, flow = self._begin(next="//external.example.com/")
        initial_session_key = self.client.session.session_key
        claims = self._claims(flow)
        response, exchange = self._callback(query, claims)
        self.assertRedirects(response, reverse("aspm_projects"), fetch_redirect_response=False)
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertEqual(len(query["code_challenge"][0]), 43)
        self.assertEqual(exchange.call_args_list[0].kwargs["data"]["code_verifier"], flow["verifier"])
        self.assertNotEqual(self.client.session.session_key, initial_session_key)
        identity = SsoIdentity.objects.get(issuer=ISSUER, subject="subject")
        self.assertNotEqual(identity.user_id, self.local.pk)
        self.assertFalse(identity.user.has_usable_password())
        self.assertFalse(identity.user.is_superuser)
        self.assertEqual(self.client.session[SESSION_KEY]["role"], "expert")
        replay = self.client.get(reverse("aspm_oidc_callback"), {"state": query["state"][0], "code": "short-code"}, secure=True)
        self.assertEqual(replay.status_code, 400)

    def test_invalid_state_nonce_issuer_audience_authorized_party_expiry_signature(self):
        self._begin()
        self.assertEqual(self.client.get(reverse("aspm_oidc_callback"), {"state": "bad", "code": "short-code"}, secure=True).status_code, 400)
        for invalid in (
            {"nonce": "foreign"}, {"iss": "https://other.example.com/realms/qualification"}, {"aud": "other"},
            {"azp": "other"}, {"exp": int(time.time()) - 1}, {"aud": ["aspm", "other"], "azp": None},
        ):
            with self.subTest(invalid=invalid):
                query, flow = self._begin()
                response, _ = self._callback(query, self._claims(flow) | invalid)
                self.assertEqual(response.status_code, 400)
        query, flow = self._begin()
        other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.assertEqual(self._callback(query, self._claims(flow), key=other)[0].status_code, 400)
        self.assertFalse(SsoIdentity.objects.exists())

    def test_logout_is_post_and_csrf_required(self):
        self.client = Client(enforce_csrf_checks=True)
        query, flow = self._begin()
        self.assertEqual(self._callback(query, self._claims(flow))[0].status_code, 302)
        logout_url = reverse("aspm_oidc_logout")
        self.assertEqual(self.client.get(logout_url, secure=True).status_code, 405)
        self.assertEqual(self.client.post(logout_url, secure=True).status_code, 403)
        csrf = self.client.cookies["csrftoken"].value
        response = self.client.post(logout_url, secure=True, HTTP_X_CSRFTOKEN=csrf, HTTP_REFERER="https://testserver/workspace/projects")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlsplit(response.url).hostname, "idp.example.com")
        self.assertNotIn(SESSION_KEY, self.client.session)


@override_settings(ASPM_OIDC_ENABLED=True, ASPM_OIDC_ISSUER=ISSUER)
class ManagedAuthorizationTests(IngestionFixture, TestCase):
    def setUp(self):
        self.setup_ingestion()
        SsoProductGrant.objects.create(issuer=ISSUER, group_id=GROUP_TEST, product=self.product)
        SsoProductGrant.objects.create(issuer=ISSUER, group_id=GROUP_PAYMENTS, product=self.hidden)
        self.scan = self.complete(self.accepted())
        self.finding = Finding.objects.get(test=self.scan.test)
        repo = Repository.objects.create(product=self.hidden, url="https://example.org/payments-api")
        self.other_commit = Commit.objects.create(repository=repo, sha="a" * 40)
        self.other_scan = ScanRun.objects.create(
            commit=self.other_commit, product=self.hidden, submitted_by=self.service, delivery_key="hidden",
            fingerprint="a" * 64, scanner=self.scan.scanner, artifact_path=self.scan.artifact_path,
            artifact_sha256=self.scan.artifact_sha256, artifact_size=self.scan.artifact_size, original_name=self.scan.original_name,
        )
        selection = CommitScanSet.objects.create(commit=self.other_commit, scan_ids=[], expected_scanners=[])
        self.other_report = GeneratedReport.objects.create(commit=self.other_commit, scan_set=selection, version=1, manifest={}, status="COMPLETED")

    def _session(self, access, groups=(), *, checked=None):
        user = get_user_model().objects.create_user(username=f"aspm-sso-{SsoIdentity.objects.count()}")
        SsoIdentity.objects.create(issuer=ISSUER, subject=user.username, user=user)
        client = Client()
        client.force_login(user, backend=BACKEND)
        session = client.session
        now = int(time.time())
        session[SESSION_KEY] = {"role": access, "groups": [str(x) for x in groups], "issuer": ISSUER, "expires": now + 120, "checked": now if checked is None else checked}
        session.save()
        return client, user

    def test_product_grants_form_union_and_reconcile_on_request(self):
        for groups, product_ids in (
            ((), []), ((GROUP_TEST,), [self.product.pk]), ((GROUP_PAYMENTS,), [self.hidden.pk]),
            ((GROUP_TEST, GROUP_PAYMENTS), [self.product.pk, self.hidden.pk]),
        ):
            with self.subTest(groups=groups):
                client, _ = self._session("user", groups)
                response = client.get(reverse("aspm_projects"))
                self.assertEqual(response.status_code, 200)
                self.assertCountEqual([item.pk for item in response.context["projects"]], product_ids)
        client, _ = self._session("user", (GROUP_TEST,))
        self.assertEqual(client.get(reverse("aspm_v1:artifact", args=(self.scan.pk,))).status_code, 200)
        self.assertEqual(client.get(reverse("aspm_v1:artifact", args=(self.other_scan.pk,))).status_code, 404)
        self.assertEqual(client.get(reverse("aspm_v1:report-download", args=(self.other_report.pk,))).status_code, 404)
        self.assertEqual(client.get(reverse("aspm_commit_evidence", args=(self.other_commit.pk,))).status_code, 404)
        self.assertEqual(client.get(reverse("product-detail", args=(self.hidden.pk,))).status_code, 404)
        self.assertContains(client.get(reverse("aspm_reports")), "No generated reports match")
        self.assertEqual(client.get(reverse("api_v3:assets_detail", args=(self.hidden.pk,))).status_code, 404)
        SsoProductGrant.objects.filter(group_id=GROUP_TEST).delete()
        self.assertEqual(client.get(reverse("aspm_v1:artifact", args=(self.scan.pk,))).status_code, 404)

    def test_workspace_filters_and_report_tabs_preserve_product_grants(self):
        client, _ = self._session("user", (GROUP_TEST,))
        projects = reverse("aspm_projects")
        visible = client.get(projects, {"product_type": self.product.prod_type_id, "q": self.product.name})
        self.assertEqual([item.pk for item in visible.context["projects"]], [self.product.pk])
        self.assertEqual(visible.context["projects"][0].latest_scan_status, self.scan.status)
        excluded = client.get(projects, {"q": self.hidden.name})
        self.assertContains(excluded, "No projects match your search.")

        reports = reverse("aspm_reports")
        originals = client.get(reports, {"type": "originals"})
        self.assertEqual([entry.pk for entry in originals.context["entries"]], [self.scan.pk])
        self.assertContains(originals, reverse("aspm_v1:artifact", args=(self.scan.pk,)))
        self.assertNotContains(originals, reverse("aspm_v1:artifact", args=(self.other_scan.pk,)))

        classic = client.get(reports, {"type": "classic"})
        self.assertEqual([entry.pk for entry in classic.context["entries"]], [self.product.pk])
        self.assertContains(classic, reverse("product_report", args=(self.product.pk,)))
        self.assertNotContains(classic, reverse("product_report", args=(self.hidden.pk,)))

    def test_repository_branch_filter_and_activity_follow_product_grants(self):
        reader, _ = self._session("user", (GROUP_TEST,))
        commit = self.scan.commit
        commit.branch = "feature/example"
        commit.save(update_fields=["branch"])
        repository = reverse("scm_repository_detail", args=(commit.repository_id,))

        scoped = reader.get(repository, {"branch": commit.branch})
        self.assertContains(scoped, self.scan.scanner)
        self.assertEqual([item.pk for item in scoped.context["commits"]], [commit.pk])
        self.assertEqual(scoped.context["latest_scan"].pk, self.scan.pk)

        empty = reader.get(repository, {"branch": "missing"})
        self.assertContains(empty, "No linked commits match this branch.")
        self.assertIsNone(empty.context["latest_scan"])
        self.assertEqual(reader.get(reverse("scm_repository_detail", args=(self.other_scan.commit.repository_id,))).status_code, 404)

    def test_role_boundaries_hold_at_legacy_and_aspm_routes(self):
        user, _ = self._session("user", (GROUP_TEST,))
        expert, _ = self._session("expert")
        secops, _ = self._session("secops")
        routes = [
            reverse("aspm_engagement_policy", args=(self.product.pk,)),
            reverse("aspm_sso_mappings"), reverse("system_settings"), reverse("aspm_webhooks"),
        ]
        for route in routes:
            self.assertEqual(user.get(route).status_code, 403)
            self.assertEqual(expert.get(route).status_code, 403)
        self.assertEqual(secops.get(routes[0]).status_code, 200)
        self.assertEqual(secops.get(routes[1]).status_code, 200)
        self.assertEqual(secops.get(routes[2]).status_code, 200)
        finding = reverse("finding-detail", args=(self.finding.pk,))
        self.assertEqual(user.patch(finding, {"false_p": True}, content_type="application/json").status_code, 403)
        self.assertEqual(user.post(reverse("aspm_create_report", args=(self.scan.commit_id,))).status_code, 403)
        self.assertEqual(user.get(reverse("view_test", args=(self.scan.test_id,))).status_code, 200)
        self.assertEqual(expert.get(reverse("product-detail", args=(self.hidden.pk,))).status_code, 200)
        self.assertEqual(expert.patch(finding, {"title": "New title"}, content_type="application/json").status_code, 403)
        response = expert.patch(finding, {"false_p": True}, content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content[:1000])
        v3 = reverse("api_v3:findings_detail", args=(self.finding.pk,))
        self.assertEqual(user.patch(v3, {"false_p": False}, content_type="application/json").status_code, 403)
        self.assertEqual(expert.patch(v3, {"title": "New title"}, content_type="application/json").status_code, 403)
        response = expert.patch(v3, {"false_p": True}, content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content[:1000])
        self.finding.refresh_from_db()
        self.assertTrue(self.finding.false_p)
        self.assertFalse(self.scan.observations.get().snapshot["false_p"])

    def test_reader_classic_scope_links_and_reports(self):
        reader, _ = self._session("user", (GROUP_TEST,))
        date = timezone.localdate()
        hidden = Engagement.objects.create(product=self.hidden, name="Hidden sibling assessment", target_start=date, target_end=date)
        hidden_test = Test.objects.create(
            engagement=hidden, test_type=self.scan.test.test_type, target_start=timezone.now(), target_end=timezone.now(),
        )
        landing = reader.get(reverse("aspm_classic"))
        self.assertContains(landing, self.product.name)
        self.assertNotContains(landing, self.hidden.name)
        for path in (reverse("product"), "/product"):
            listing = reader.get(path, follow=True)
            self.assertContains(listing, self.product.name)
            self.assertNotContains(listing, self.hidden.name)
        types = reader.get(reverse("view_product_type", args=(self.product.prod_type_id,)))
        self.assertContains(types, self.product.name)
        self.assertNotContains(types, self.hidden.name)
        classic = reader.get(reverse("view_test", args=(self.scan.test_id,)))
        self.assertContains(classic, "View originating ScanRun and commit")
        evidence = reader.get(reverse("aspm_commit_evidence", args=(self.scan.commit_id,)), {"tab": "originals", "run": str(self.scan.pk)})
        self.assertContains(evidence, reverse("view_test", args=(self.scan.test_id,)))
        self.assertContains(evidence, reverse("view_engagement", args=(self.scan.test.engagement_id,)))
        self.assertEqual(reader.get(reverse("view_test", args=(hidden_test.pk,))).status_code, 404)
        for url in (reverse("test-detail", args=(hidden_test.pk,)), reverse("api_v3:tests_detail", args=(hidden_test.pk,))):
            self.assertEqual(reader.get(url).status_code, 404)
        self.assertEqual(reader.get(reverse("test_report", args=(hidden_test.pk,))).status_code, 403)
        report = reader.get(reverse("test_report", args=(self.scan.test_id,)), {"_generate": "1", "report_type": "HTML"})
        self.assertContains(report, self.finding.title)
        self.assertEqual(reader.post(reverse("test-detail", args=(self.scan.test_id,))).status_code, 403)
        self.assertEqual(reader.post(reverse("importscan-list"), {}).status_code, 403)

    def test_expert_classic_import_reimport_and_manual_finding_share_product(self):
        expert, _ = self._session("expert")
        date = timezone.localdate().isoformat()
        result = expert.post(reverse("engagement-list"), {
            "name": "Pentest without Git", "product": self.product.pk, "target_start": date, "target_end": date,
        }, content_type="application/json")
        self.assertEqual(result.status_code, 201, result.content[:1200])
        engagement = result.json()["id"]
        payload = {"mode": "import", "scan_type": self.scan.scanner, "engagement": engagement}
        first = expert.post(reverse("api_v3:import"), {**payload, "file": SimpleUploadedFile("scan.json", generic("Classic finding"))})
        self.assertEqual(first.status_code, 200, first.content[:1200])
        test = Test.objects.get(engagement_id=engagement)
        second = expert.post(reverse("reimportscan-list"), {
            "test": test.pk, "scan_type": self.scan.scanner, "deduplication_execution_mode": "sync",
            "file": SimpleUploadedFile("scan.json", generic("Classic finding")),
        })
        self.assertEqual(second.status_code, 201, second.content[:1200])
        manual = expert.post(reverse("finding-list"), {
            "test": test.pk, "title": "Manual assessment", "severity": "Low", "description": "Manual test fixture",
            "numerical_severity": "S3", "found_by": [], "active": True, "verified": False,
        }, content_type="application/json")
        self.assertEqual(manual.status_code, 201, manual.content[:1200])
        self.assertIsNone(test.engagement.commit_id)
        self.assertFalse(ScanRun.objects.filter(test=test).exists())
        self.assertEqual(test.engagement.product_id, self.scan.product_id)
        self.assertNotContains(expert.get(reverse("view_test", args=(test.pk,))), "View originating ScanRun and commit")
        self.assertEqual(expert.get(reverse("aspm_classic")).status_code, 200)
        self.assertEqual(expert.get(reverse("product_type")).status_code, 200)
        self.assertEqual(expert.get(reverse("system_settings")).status_code, 403)

    def test_secops_classic_creation_uses_existing_endpoints(self):
        secops, _ = self._session("secops")
        options = {"content_type": "application/json"}
        product_type = secops.post(reverse("product_type-list"), {"name": "Risk assessments"}, **options)
        self.assertEqual(product_type.status_code, 201, product_type.content[:1200])
        product = secops.post(reverse("product-list"), {
            "name": "Infrastructure", "description": "Legacy team fixture", "prod_type": product_type.json()["id"],
        }, **options)
        self.assertEqual(product.status_code, 201, product.content[:1200])
        date = timezone.localdate().isoformat()
        engagement = secops.post(reverse("engagement-list"), {
            "name": "Network review", "product": product.json()["id"], "target_start": date, "target_end": date,
        }, **options)
        self.assertEqual(engagement.status_code, 201, engagement.content[:1200])
        moment = timezone.now().isoformat()
        test = secops.post(reverse("test-list"), {
            "engagement": engagement.json()["id"], "test_type": self.scan.test.test_type_id,
            "target_start": moment, "target_end": moment,
        }, **options)
        self.assertEqual(test.status_code, 201, test.content[:1200])
        self.assertEqual(secops.get(reverse("view_test", args=(test.json()["id"],))).status_code, 200)

    def test_expiry_deactivation_and_existing_managed_tokens(self):
        client, _ = self._session("secops", checked=int(time.time()) - 300)
        self.assertEqual(client.get(reverse("aspm_v1:scan-detail", args=(self.scan.pk,))).status_code, 403)
        self.assertNotIn(SESSION_KEY, client.session)
        client, account = self._session("expert")
        raw = Token.objects.create(user=account)
        response = Client().get(reverse("finding-detail", args=(self.finding.pk,)), HTTP_AUTHORIZATION=f"Token {raw.key}")
        self.assertIn(response.status_code, {401, 403})
        account.is_active = False
        account.save(update_fields=["is_active"])
        self.assertEqual(client.get(reverse("aspm_projects")).status_code, 302)
        self.assertNotIn(SESSION_KEY, client.session)
