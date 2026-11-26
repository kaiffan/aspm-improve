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

    def test_storage_threshold_uses_decimal_integer_environment_values(self):
        for args, expected in (((), "1073741824"), (("--set", "storage.minimumFreeBytes=5368709120"), "5368709120")):
            with self.subTest(expected=expected):
                migration = next(doc for doc in render(*args) if doc["kind"] == "Job")
                container = migration["spec"]["template"]["spec"]["containers"][0]
                threshold = next(env["value"] for env in container["env"] if env["name"] == "DD_ASPM_STORAGE_MIN_FREE_BYTES")
                self.assertEqual(threshold, expected)

    def test_component_switches(self):
        for component in ("web", "worker", "beat", "migrations"):
            with self.subTest(component=component):
                docs = render("--set", f"{component}.enabled=false")
                self.assertFalse(any(x["metadata"].get("labels", {}).get("app.kubernetes.io/component") == ("migration" if component == "migrations" else component) for x in docs))
                if component == "web":
                    self.assertFalse(any(x["kind"] in {"Service", "Ingress", "HorizontalPodAutoscaler", "PodDisruptionBudget"} for x in docs))

    def test_profiles(self):
        for profile in ("dev", "staging", "production.example", "local", "ha", "high-throughput"):
            with self.subTest(profile=profile):
                self.assertTrue(render("-f", str(CHART / f"values-{profile}.yaml")))

    def test_ha_schedules_and_protects_each_component(self):
        docs = render("-f", str(CHART / "values-ha.yaml"))
        by_kind = {kind: {doc["metadata"]["name"].rsplit("-", 1)[-1]: doc["spec"] for doc in docs if doc["kind"] == kind}
                   for kind in ("Deployment", "PodDisruptionBudget")}
        for component, replicas, min_available in (("web", 2, 1), ("worker", 3, 2)):
            deployment = by_kind["Deployment"][component]
            disruption = by_kind["PodDisruptionBudget"][component]
            self.assertEqual(deployment["replicas"], replicas)
            self.assertEqual(disruption["minAvailable"], min_available)
            self.assertEqual(disruption["selector"], deployment["selector"])
            spread = deployment["template"]["spec"]["topologySpreadConstraints"]
            self.assertCountEqual([rule["topologyKey"] for rule in spread], ["kubernetes.io/hostname", "topology.kubernetes.io/zone"])
            self.assertTrue(all(rule["labelSelector"] == deployment["selector"] for rule in spread))
        self.assertEqual(by_kind["Deployment"]["beat"]["strategy"], {"type": "Recreate"})

    def test_lab_ingress_requires_neither_cluster_class_nor_unrelated_source_pods(self):
        profile = Path(__file__).resolve().parents[3] / "labs" / "orbstack" / "values-ha-ingress.yaml"
        docs = render("-f", str(profile), "--set", "ingress.enabled=true",
                      "--set-string", "ingress.className=",
                      "--set-string", r"ingress.annotations.kubernetes\.io/ingress\.class=aspm-ha-lab")
        ingress = next(doc for doc in docs if doc["kind"] == "Ingress")
        self.assertNotIn("ingressClassName", ingress["spec"])
        self.assertEqual(ingress["metadata"]["annotations"]["kubernetes.io/ingress.class"], "aspm-ha-lab")
        policy = next(doc for doc in docs if doc["kind"] == "NetworkPolicy")
        ingress_source = policy["spec"]["ingress"][0]["from"][0]
        self.assertIn("namespaceSelector", ingress_source)
        self.assertIn("podSelector", ingress_source)

    def test_high_throughput_scales_web_and_opt_in_workers(self):
        profile = ("-f", str(CHART / "values-high-throughput.yaml"))
        for worker_autoscaling in (False, True):
            docs = render(*profile, "--set", f"worker.hpa.enabled={str(worker_autoscaling).lower()}")
            hpas = {doc["spec"]["scaleTargetRef"]["name"] for doc in docs if doc["kind"] == "HorizontalPodAutoscaler"}
            for deployment in (doc for doc in docs if doc["kind"] == "Deployment"):
                with self.subTest(name=deployment["metadata"]["name"]):
                    self.assertEqual("replicas" not in deployment["spec"], deployment["metadata"]["name"] in hpas)
            self.assertEqual(len(hpas), 2 if worker_autoscaling else 1)

    def test_external_postgresql_overlay_reaches_every_database_client(self):
        docs = render("-f", str(CHART / "values-external-postgresql.example.yaml"))
        self.assertFalse(any(doc["kind"] in {"Secret", "StatefulSet"} for doc in docs))
        checked = []
        for doc in docs:
            if doc["kind"] not in {"Deployment", "Job"}:
                continue
            pod = doc["spec"]["template"]["spec"]
            for container in pod.get("initContainers", []) + pod["containers"]:
                if container["name"] == "nginx":
                    continue
                env = {entry["name"]: entry for entry in container["env"]}
                self.assertEqual(env["DD_DATABASE_URL"]["valueFrom"]["secretKeyRef"], {"name": "aspm-runtime", "key": "database-url"})
                db_options = json.loads(env["DD_DATABASE_OPTIONS"]["value"])
                self.assertEqual(db_options, {"connect_timeout": 5, "sslmode": "verify-full", "sslrootcert": "/app/db-tls/ca.crt"})
                self.assertIn({"name": "db-tls", "mountPath": "/app/db-tls", "readOnly": True}, container["volumeMounts"])
                checked.append(container["name"])
            self.assertEqual(next(v["secret"]["secretName"] for v in pod["volumes"] if v["name"] == "db-tls"), "aspm-postgres-ca")
        self.assertEqual(len(checked), 7)

    def test_http_smoke_uses_service_and_nginx_readiness_matches_target_port(self):
        docs = render("--set", "service.port=8090", "--set", "tests.enabled=true", "--set", "image.pullPolicy=Never")
        service, = (doc for doc in docs if doc["kind"] == "Service")
        pod, = (doc for doc in docs if doc["kind"] == "Pod")
        hook = pod["spec"]["containers"][0]
        self.assertIn(f'http://{service["metadata"]["name"]}:8090/login', hook["args"][0])
        self.assertEqual(hook["imagePullPolicy"], "Never")
        web, = (doc for doc in docs if doc["kind"] == "Deployment" and doc["metadata"]["name"].endswith("-web"))
        template = web["spec"]["template"]
        nginx = next(c for c in template["spec"]["containers"] if c["name"] == "nginx")
        self.assertEqual(nginx["readinessProbe"]["httpGet"]["port"], service["spec"]["ports"][0]["targetPort"])
        self.assertTrue(all(template["metadata"]["labels"][key] == value for key, value in service["spec"]["selector"].items()))

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
