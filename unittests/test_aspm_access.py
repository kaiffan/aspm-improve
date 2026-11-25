import json
import secrets
import time
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token

from dojo.aspm_access.backend import BACKEND
from dojo.aspm_access.middleware import FLOW_KEY, SESSION_KEY
from dojo.aspm_access.models import SsoIdentity, SsoProductGrant
from dojo.aspm_ingestion.models import CommitScanSet, GeneratedReport, ScanRun
from dojo.models import Finding
from dojo.scm.models import Commit, Repository
from unittests.test_aspm_ingestion import IngestionFixture

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
        self.assertEqual(user.get(reverse("view_test", args=(self.scan.test_id,))).status_code, 403)
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
