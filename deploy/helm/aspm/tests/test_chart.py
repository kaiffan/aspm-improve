"""Offline behavioral chart tests; run with Python unittest and a local Helm binary."""
# ruff: noqa: INP001, S607 -- standalone CLI helpers invoke installed git/helm tools
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import jsonschema
import yaml

CHART = Path(__file__).resolve().parents[1]


def render(*args, chart=CHART):
    result = subprocess.run(["helm", "template", "qualification", str(chart), "--namespace", "aspm-test", *args], capture_output=True, text=True, check=True)
    return [item for item in yaml.safe_load_all(result.stdout) if item]


class ChartTests(unittest.TestCase):
    def test_defaults_use_external_dependencies_and_secret_references(self):
        manifests = render()
        self.assertFalse(any(x["kind"] in {"StatefulSet", "Secret", "PersistentVolumeClaim"} for x in manifests))
        for manifest in manifests:
            if manifest["kind"] not in {"Deployment", "Job"}:
                continue
            spec = manifest["spec"]["template"]["spec"]
            self.assertFalse(spec["automountServiceAccountToken"])
            for container in spec["containers"]:
                self.assertTrue(container["securityContext"]["readOnlyRootFilesystem"])
                self.assertFalse(container["securityContext"]["allowPrivilegeEscalation"])
                self.assertEqual(container["securityContext"]["capabilities"]["drop"], ["ALL"])
                for env in container.get("env", []):
                    if env["name"] in {"DD_SECRET_KEY", "DD_DATABASE_URL", "DD_CELERY_BROKER_URL", "DD_CACHE_URL", "DD_CREDENTIAL_AES_256_KEY"}:
                        self.assertIn("secretKeyRef", env["valueFrom"])

    def test_workload_contract(self):
        manifests = render()
        deployments = {x["metadata"]["name"].rsplit("-", 1)[-1]: x for x in manifests if x["kind"] == "Deployment"}
        self.assertEqual(set(deployments), {"web", "worker", "beat"})
        self.assertEqual(deployments["beat"]["spec"]["replicas"], 1)
        self.assertEqual(deployments["beat"]["spec"]["strategy"]["type"], "Recreate")
        worker = deployments["worker"]["spec"]["template"]["spec"]
        self.assertGreater(worker["terminationGracePeriodSeconds"], 900)
        self.assertIn("--prefetch-multiplier=1", worker["containers"][0]["args"])
        for deployment in deployments.values():
            spec = deployment["spec"]["template"]["spec"]
            self.assertIn("aspm_preflight", spec["initContainers"][0]["command"])
            self.assertEqual(next(v["persistentVolumeClaim"]["claimName"] for v in spec["volumes"] if v["name"] == "evidence"), "aspm-evidence")
        web = deployments["web"]["spec"]["template"]["spec"]["containers"][0]
        paths = {web[key]["httpGet"]["path"] for key in ("startupProbe", "readinessProbe", "livenessProbe")}
        self.assertEqual(len(paths), 3)

    def test_nginx_temp_paths_are_on_the_writable_mount(self):
        config = next(x["data"]["nginx.conf"] for x in render() if x["kind"] == "ConfigMap")
        for directive in ("client_body", "proxy", "uwsgi", "fastcgi", "scgi"):
            with self.subTest(directive=directive):
                self.assertIn(f"{directive}_temp_path /tmp/", config)

    def test_migrations_are_separate_fenced_hook(self):
        job = next(x for x in render() if x["kind"] == "Job")
        self.assertEqual(job["metadata"]["annotations"]["helm.sh/hook"], "pre-install,pre-upgrade")
        self.assertEqual(job["spec"]["backoffLimit"], 0)
        self.assertIn("aspm_migrate", job["spec"]["template"]["spec"]["containers"][0]["command"])

    def test_component_switches(self):
        for component in ("web", "worker", "beat", "migrations"):
            with self.subTest(component=component):
                docs = render("--set", f"{component}.enabled=false")
                self.assertFalse(any(x["metadata"].get("labels", {}).get("app.kubernetes.io/component") == ("migration" if component == "migrations" else component) for x in docs))
                if component == "web":
                    self.assertFalse(any(x["kind"] in {"Service", "Ingress", "HorizontalPodAutoscaler", "PodDisruptionBudget"} for x in docs))

    def test_profiles(self):
        for profile in ("dev", "staging", "production.example"):
            with self.subTest(profile=profile):
                self.assertTrue(render("-f", str(CHART / f"values-{profile}.yaml")))

    def test_hpa_tls_and_monitoring_opt_in(self):
        docs = render("--set", "hpa.enabled=true", "--set", "ingress.enabled=true", "--set", "monitoring.serviceMonitor.enabled=true")
        kinds = {x["kind"] for x in docs}
        self.assertTrue({"HorizontalPodAutoscaler", "Ingress", "ServiceMonitor"} <= kinds)
        monitor = next(x for x in docs if x["kind"] == "ServiceMonitor")
        self.assertEqual(monitor["spec"]["endpoints"][0]["path"], "/django_metrics/metrics")
        web = next(x for x in docs if x["kind"] == "Deployment" and x["metadata"]["name"].endswith("-web"))
        self.assertNotIn("replicas", web["spec"])
        ingress = next(x for x in docs if x["kind"] == "Ingress")
        self.assertTrue(ingress["spec"]["tls"][0]["secretName"])

    def test_packaged_chart_contains_opt_in_http_smoke_hook(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(["helm", "package", str(CHART), "-d", directory], capture_output=True, text=True, check=True)
            package, = Path(directory).glob("aspm-*.tgz")
            self.assertFalse(any(doc["kind"] == "Pod" for doc in render(chart=package)))
            pod, = (doc for doc in render("--set", "tests.enabled=true", chart=package) if doc["kind"] == "Pod")
            self.assertEqual(pod["metadata"]["annotations"]["helm.sh/hook"], "test")
            self.assertEqual(pod["metadata"]["labels"]["app.kubernetes.io/component"], "test")

    def test_names_digest_and_replica_settings(self):
        digest = "sha256:" + "a" * 64
        docs = render("--set", "fullnameOverride=custom", "--set", "web.replicas=4", "--set", f"image.digest={digest}")
        web = next(x for x in docs if x["kind"] == "Deployment" and x["metadata"]["name"] == "custom-web")
        self.assertEqual(web["spec"]["replicas"], 4)
        self.assertEqual(web["spec"]["template"]["spec"]["containers"][0]["image"], "aspm/django@" + digest)

    def test_invalid_values_are_rejected(self):
        for value in ("worker.replicas=0", "web.enabled=banana", "image.digest=latest", "service.port=70000", "existingSecret=", "unknown=true"):
            with self.subTest(value=value):
                result = subprocess.run(["helm", "template", "q", str(CHART), "--set", value], capture_output=True, text=True, check=False)
                self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_oidc_client_credential_is_web_only(self):
        docs = render(
            "--set", "oidc.enabled=true",
            "--set", "oidc.issuer=https://idp.example.invalid/realms/aspm",
            "--set", "oidc.callbackUrl=https://aspm.example.invalid/sso/callback",
            "--set", "oidc.clientId=aspm",
            "--set", "oidc.existingSecret=aspm-keycloak",
            "--set", "oidc.existingCaSecret=aspm-keycloak-ca",
        )
        oidc = []
        for doc in docs:
            if doc["kind"] not in {"Deployment", "Job"}:
                continue
            pod = doc["spec"]["template"]["spec"]
            for container in (*pod["containers"], *pod.get("initContainers", [])):
                oidc.extend(
                    (container["name"], value["valueFrom"]["secretKeyRef"])
                    for value in container.get("env", []) if value["name"] == "DD_ASPM_OIDC_CLIENT_SECRET"
                )
        self.assertEqual(oidc, [("web", {"name": "aspm-keycloak", "key": "oidc-client-secret"})])
        with self.assertRaises(subprocess.CalledProcessError):
            render("--set", "oidc.enabled=true")
        with self.assertRaises(subprocess.CalledProcessError):
            render("--set", "config.DD_ASPM_OIDC_CLIENT_SECRET=invalid")

    def test_schema_matches_defaults(self):
        schema = json.loads((CHART / "values.schema.json").read_text())
        jsonschema.Draft7Validator.check_schema(schema)
        jsonschema.validate(yaml.safe_load((CHART / "values.yaml").read_text()), schema)

    def test_network_policy_denies_unconfigured_dependencies(self):
        policy = next(x for x in render() if x["kind"] == "NetworkPolicy")
        self.assertEqual(policy["spec"]["policyTypes"], ["Ingress", "Egress"])
        self.assertEqual(len(policy["spec"]["egress"]), 1)
        self.assertEqual({p["port"] for p in policy["spec"]["egress"][0]["ports"]}, {53})


if __name__ == "__main__":
    unittest.main(verbosity=2)
