#!/usr/bin/env python3
"""Operate on a single explicitly selected Kubernetes release."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
import uuid

import yaml


ROOT = Path(__file__).resolve().parents[1]
PROBE = r"""
import json, os, pathlib, ssl, tempfile, urllib.request
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dojo.settings.settings")
import django, redis
django.setup()
from django.db import connection
from dojo.management.commands.aspm_preflight import storage_ready

def db():
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        assert cursor.fetchone() == (1,)

def ping(name):
    return redis.Redis.from_url(os.environ[name], socket_connect_timeout=5, socket_timeout=5).ping()

def media():
    with tempfile.NamedTemporaryFile(dir="/app/media") as f:
        f.write(b"aspm preflight"); f.flush(); os.fsync(f.fileno())

def oidc():
    issuer = os.environ.get("DD_ASPM_OIDC_ISSUER")
    if issuer:
        ca = os.environ.get("DD_ASPM_OIDC_CA_BUNDLE")
        with urllib.request.urlopen(issuer + "/.well-known/openid-configuration",
                                    context=ssl.create_default_context(cafile=ca), timeout=8) as response:
            assert json.load(response)["issuer"] == issuer

checks = {"PostgreSQL SQL/TLS": db, "broker DNS/PING": lambda: ping("DD_CELERY_BROKER_URL"),
          "cache DNS/PING": lambda: ping("DD_CACHE_URL"), "evidence fsync/rename": storage_ready,
          "media write": media, "OIDC discovery": oidc}
ok = True
for name, check in checks.items():
    if name == "OIDC discovery" and not os.environ.get("DD_ASPM_OIDC_ISSUER"):
        print(name + ": DISABLED", flush=True); continue
    try:
        check()
        print(name + ": OK", flush=True)
    except Exception as exc:
        print(name + ": FAILED (" + type(exc).__name__ + ")", flush=True)
        ok = False
raise SystemExit(0 if ok else 1)
"""


def run(*command, capture=False, input_text=None):
    return subprocess.run(command, check=True, text=True, input=input_text,
                          stdout=subprocess.PIPE if capture else None).stdout


def kube(args, *command, **kwargs):
    return run("kubectl", "--context", args.context, "--namespace", args.namespace, *command, **kwargs)


def helm(args, command, *other, **kwargs):
    return run("helm", command, *other, "--kube-context", args.context, "--namespace", args.namespace, **kwargs)


def profile(args):
    files = ["-f", str(ROOT / "config" / f"values-{args.profile}.yaml")]
    for value in args.values:
        files.extend(("-f", value))
    return [*files, "--set-string", rf"nodeSelector.kubernetes\.io/arch={args.arch}"]


def label(args, obj):
    return obj.get("metadata", {}).get("labels", {}).get("app.kubernetes.io/instance") == args.release


def context(args):
    namespace = json.loads(kube(args, "get", "namespace", args.namespace, "-o", "json", capture=True))
    if args.profile == "local" and namespace["metadata"].get("labels", {}).get("aspm-lab") != "true":
        raise ValueError("The local profile requires the namespace label aspm-lab=true.")
    nodes = json.loads(kube(args, "get", "nodes", "-o", "json", capture=True))["items"]
    ready = []
    for node in nodes:
        status = node["status"]
        conditions = {c["type"]: c["status"] for c in status["conditions"]}
        if conditions.get("Ready") == "True" and not node["spec"].get("unschedulable"):
            node_info = status["nodeInfo"]
            resource = status["allocatable"]
            print(f"{node['metadata']['name']}: {node_info['operatingSystem']}/{node_info['architecture']}, "
                  f"{resource['cpu']} CPU, {resource['memory']} memory; DiskPressure={conditions.get('DiskPressure')}",
                  flush=True)
            if node_info["operatingSystem"] == "linux" and node_info["architecture"] == args.arch:
                if conditions.get("DiskPressure") != "True" and conditions.get("MemoryPressure") != "True":
                    ready.append(node)
    if not ready:
        raise ValueError(f"No Ready Linux/{args.arch} nodes without disk or memory pressure.")


def get(args, kind, name):
    return json.loads(kube(args, "get", kind, name, "-o", "json", capture=True))


def require_secret_keys(args, secrets):
    for name, required in sorted(secrets.items()):
        # Keep Secret values out of the subprocess stdout and logs.
        keys = kube(args, "get", "secret", name, "-o",
                    r'go-template={{range $k, $v := .data}}{{$k}}{{"\n"}}{{end}}', capture=True).splitlines()
        if required.difference(keys):
            raise ValueError(f"Secret {name} is missing expected keys: {', '.join(sorted(required.difference(keys)))}.")
        print(f"Secret {name}: references present", flush=True)


def get_manifest(args):
    run("helm", "lint", "--strict", str(args.chart), *profile(args))
    rendered = helm(args, "template", args.release, str(args.chart), "--dry-run=server", *profile(args), capture=True)
    return [item for item in yaml.safe_load_all(rendered) if item]


def env_map(container):
    return {entry["name"]: entry.get("value") for entry in container["env"] if "value" in entry}


def web_containers(spec):
    named = {container["name"]: container for container in spec["containers"]}
    return named["web"], named["nginx"]


def require_manifest_secrets(args, manifest, secrets):
    prom_configs = [
        item["data"]["prometheus.yml"] for item in manifest
        if item["kind"] == "ConfigMap" and "prometheus.yml" in item.get("data", {})
    ]
    prom_config = "\n".join(prom_configs)
    volume_keys = {
        "db-tls": {"ca.crt"}, "oidc-ca": {"ca.crt"}, "ca": {"ca.crt"},
        "scrape-auth": {"token"}, "scrape-tls": {"tls.crt", "tls.key"},
        "scrape-ca": {"ca.crt"},
        "write-auth": {name for name in ("username", "password", "token")
                       if f"/etc/aspm-write-auth/{name}" in prom_config},
        "write-tls": {name for name in ("ca.crt", "tls.crt", "tls.key")
                      if f"/etc/aspm-write-tls/{name}" in prom_config},
    }
    for item in manifest:
        if item["kind"] in {"Deployment", "StatefulSet", "Job"}:
            spec = item["spec"]["template"]["spec"]
        elif item["kind"] == "Pod":
            spec = item["spec"]
        elif item["kind"] in {"ServiceMonitor", "PodMonitor"}:
            endpoints = item["spec"].get("endpoints", item["spec"].get("podMetricsEndpoints", []))
            for endpoint in endpoints:
                for ref in (
                    endpoint.get("authorization", {}).get("credentials"),
                    endpoint.get("tlsConfig", {}).get("ca", {}).get("secret"),
                ):
                    if ref:
                        secrets.setdefault(ref["name"], set()).add(ref["key"])
            continue
        else:
            continue
        for volume in spec.get("volumes", []):
            if ref := volume.get("secret"):
                secrets.setdefault(ref["secretName"], set()).update(volume_keys.get(volume["name"], set()))
        for ref in spec.get("imagePullSecrets", []):
            secrets.setdefault(ref["name"], set()).add(".dockerconfigjson")
        for container in spec.get("containers", []) + spec.get("initContainers", []):
            for entry in container.get("env", []):
                if ref := entry.get("valueFrom", {}).get("secretKeyRef"):
                    if not ref.get("optional"):
                        secrets.setdefault(ref["name"], set()).add(ref["key"])
    require_secret_keys(args, secrets)


def packaged_chart():
    manifest = json.loads((ROOT / "DELIVERY_MANIFEST.json").read_text())
    chart = (ROOT / manifest["chart"]).resolve()
    if not chart.is_relative_to(ROOT) or not chart.is_file():
        raise ValueError("The chart listed in the delivery manifest is missing")
    if hashlib.sha256(chart.read_bytes()).hexdigest() != manifest["chart_sha256"]:
        raise ValueError("The packaged Helm chart failed its SHA-256 check")
    return chart


def validate_preflight(args, manifest):
    by_kind = lambda kind: [item for item in manifest if item["kind"] == kind]
    web, = [item for item in by_kind("Deployment") if item["metadata"].get("labels", {}).get("app.kubernetes.io/component") == "web"]
    pods = web["spec"]["template"]
    spec = pods["spec"]
    django, nginx = web_containers(spec)
    env = env_map(django)
    site = urlsplit(env["DD_SITE_URL"])
    if not site.hostname or site.scheme not in ("http", "https") or site.hostname.endswith(".invalid"):
        raise ValueError("Set DD_SITE_URL to the actual endpoint.")
    if not by_kind("Job") or not any(item["metadata"].get("annotations", {}).get("helm.sh/hook") == "test"
                                     for item in by_kind("Pod")):
        raise ValueError("Enable migrations and Helm tests for this deployment path.")
    if args.profile != "local":
        if any("@sha256:" not in c["image"] or ".invalid/" in c["image"] for c in (django, nginx)):
            raise ValueError("HA profiles require both approved image repositories with immutable sha256 digests.")
        if site.scheme != "https" or not by_kind("Ingress"):
            raise ValueError("HA profiles require a real HTTPS site with Ingress.")
        if json.loads(env.get("DD_DATABASE_OPTIONS", "{}")).get("sslmode") != "verify-full":
            raise ValueError("HA profiles require DD_DATABASE_OPTIONS sslmode=verify-full.")
    secrets = {}
    volumes = spec["volumes"]
    for v in volumes:
        if source := v.get("persistentVolumeClaim"):
            name = source["claimName"]
            pvc = get(args, "pvc", name)
            if args.profile != "local" and "ReadWriteMany" not in pvc["spec"]["accessModes"]:
                raise ValueError(f"Claim {name} must request ReadWriteMany for HA.")
            if storage_class := pvc["spec"].get("storageClassName"):
                get(args, "storageclass", storage_class)
            print(f"PVC {name}: {pvc.get('status', {}).get('phase', 'unbound')}", flush=True)
    for kind in by_kind("Ingress"):
        ingress = kind["spec"]
        if cls := ingress.get("ingressClassName"):
            get(args, "ingressclass", cls)
        if site.hostname not in {rule["host"] for rule in ingress["rules"]}:
            raise ValueError("DD_SITE_URL and Ingress host disagree.")
        for item in ingress.get("tls", []):
            secrets.setdefault(item["secretName"], set()).update(("tls.crt", "tls.key"))
    require_manifest_secrets(args, manifest, secrets)
    return pods, site.geturl()


def probe_dependencies(args, pods):
    spec = pods["spec"]
    django, nginx = web_containers(spec)
    name = "aspm-preflight-" + uuid.uuid4().hex[:10]
    selected = {k: spec[k] for k in ("securityContext", "imagePullSecrets", "nodeSelector", "tolerations", "affinity") if k in spec}
    selected.setdefault("nodeSelector", {})["kubernetes.io/arch"] = args.arch
    volumes = [v for v in spec["volumes"] if "configMap" not in v]
    selected.update(automountServiceAccountToken=False, restartPolicy="Never", activeDeadlineSeconds=120, volumes=volumes,
                    initContainers=[{k: nginx[k] for k in ("name", "image", "imagePullPolicy", "securityContext", "resources")}
                                    | {"command": ["nginx", "-v"]}])
    probe = PROBE
    if any(container["name"] == "metrics" for container in spec["containers"]):
        probe = (
            "import importlib.util\n"
            "if importlib.util.find_spec('dojo.aspm_observability') is None:\n"
            "    raise SystemExit('Monitoring is enabled. Rebuild the Django image with build-images.sh --monitoring.')\n"
            "print('Django monitoring runtime: OK', flush=True)\n"
            + probe
        )
    selected["containers"] = [{k: django[k] for k in
                               ("name", "image", "imagePullPolicy", "securityContext", "resources", "env", "volumeMounts")}
                              | {"command": ["python", "-c", probe]}]
    obj = {"apiVersion": "v1", "kind": "Pod",
           "metadata": {"name": name, "labels": pods["metadata"]["labels"] | {"app.kubernetes.io/component": "preflight"}},
           "spec": selected}
    kube(args, "create", "-f", "-", input_text=json.dumps(obj))
    try:
        waits = subprocess.run(["kubectl", "--context", args.context, "-n", args.namespace, "wait",
                                "--for=jsonpath={.status.phase}=Succeeded", f"pod/{name}", "--timeout=125s"], check=False)
        if waits.returncode:
            kube(args, "get", "pod", name, "-o", "wide")
        kube(args, "logs", name, "-c", django["name"])
        waits.check_returncode()
    finally:
        kube(args, "delete", "pod", name, "--ignore-not-found", "--wait=false")


def preflight(args):
    context(args)
    manifest = get_manifest(args)
    pods, url = validate_preflight(args, manifest)
    objects = [item for item in manifest if not item["metadata"].get("annotations", {}).get("helm.sh/hook")]
    kube(args, "apply", "--dry-run=server", "--validate=strict", "-f", "-",
         input_text=yaml.safe_dump_all(objects))
    probe_dependencies(args, pods)
    return url


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def smoke(args, url):
    deployments = json.loads(kube(args, "get", "deployment", "-l", f"app.kubernetes.io/instance={args.release}",
                                  "-o", "json", capture=True))["items"]
    workloads = {obj["metadata"]["labels"]["app.kubernetes.io/component"]: obj["metadata"]["name"]
                 for obj in deployments if label(args, obj)}
    for app in ("web", "worker", "beat"):
        kube(args, "rollout", "status", f"deployment/{workloads[app]}", f"--timeout={args.timeout}")
    kube(args, "exec", f"deployment/{workloads['web']}", "-c", "web", "--",
         "python", "manage.py", "aspm_preflight")
    kube(args, "exec", f"deployment/{workloads['worker']}", "-c", "worker", "--",
         "sh", "-ec", 'celery --app=dojo inspect --timeout=5 --destination="celery@$HOSTNAME" ping')
    kube(args, "exec", f"deployment/{workloads['web']}", "-c", "web", "--", "python", "-c",
         'import urllib.request; u="http://localhost:8081/health/"; '
         'print([(p, urllib.request.urlopen(u+p, timeout=10).status) for p in ("live","startup","ready")])')
    helm(args, "test", args.release, "--logs", "--timeout", "3m")
    if url:
        with urlopen(url.rstrip("/") + "/login", timeout=15) as response:
            if response.status != 200 or b"csrfmiddlewaretoken" not in response.read(1048576):
                raise ValueError("The published /login endpoint did not return the expected login form.")
        print(f"Login HTTP 200 at {url}", flush=True)
        if args.token_file:
            if not args.scan_id:
                raise ValueError("--token-file requires --scan-id for the read-only scoped API check.")
            uuid.UUID(args.scan_id)
            request = Request(url.rstrip("/") + f"/api/aspm/v1/scans/{args.scan_id}/",
                              headers={"Authorization": "ASPM " + args.token_file.read_text().strip()})
            with build_opener(NoRedirect()).open(request, timeout=15) as response:
                if str(json.load(response)["id"]) != args.scan_id:
                    raise ValueError("Unexpected ScanRun identity.")
            print("Scoped ScanRun GET: OK", flush=True)
    else:
        print("Published HTTP/TLS check deferred. Supply --url when ingress or port-forward is ready.", flush=True)


def deployed(args):
    return json.loads(helm(args, "status", args.release, "-o", "json", capture=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog="Exit 0: completed. Exit 1: check failed. Exit 2: invalid arguments.")
    parser.add_argument("operation", choices=("preflight", "deploy", "smoke", "rollback"))
    for field in ("context", "namespace", "release"):
        parser.add_argument(f"--{field}", required=True)
    parser.add_argument("--profile", required=True, choices=("local", "ha", "high-throughput"))
    parser.add_argument("--arch", required=True, choices=("arm64", "amd64"))
    parser.add_argument("--chart", type=Path)
    parser.add_argument("-f", "--values", action="append", default=[])
    parser.add_argument("--timeout", default="35m")
    parser.add_argument("--url", help="Published URL with a trusted certificate, or a local lab port-forward.")
    parser.add_argument("--token-file", type=Path)
    parser.add_argument("--scan-id")
    parser.add_argument("--apply", action="store_true", help="Authorize install or upgrade for the explicit target.")
    parser.add_argument("--revision", type=int)
    parser.add_argument("--schema-review", type=Path, help="Reviewed record of DB schema compatibility, backup and decision.")
    parser.add_argument("--confirm-target", help="Exact context/namespace/release/revision.")
    args = parser.parse_args()
    if args.chart is None and args.operation in ("deploy", "preflight"):
        args.chart = packaged_chart()
    if not re.fullmatch(r"[1-9][0-9]*[ms]", args.timeout):
        parser.error("timeout must be a nonzero number followed by m or s")
    if args.url:
        parsed = urlsplit(args.url)
        if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            parser.error("--url requires a host and cannot carry credentials, query or fragment")
        if parsed.scheme != "https" and (args.profile != "local" or parsed.scheme != "http"):
            parser.error("--url requires HTTPS unless using the local lab profile")
    if args.operation == "preflight":
        preflight(args)
    elif args.operation == "deploy":
        if not args.apply:
            parser.error("deployment requires --apply and an explicit context, namespace and release")
        url = preflight(args)
        helm(args, "upgrade", "--install", args.release, str(args.chart), *profile(args),
             "--reset-values", "--wait", "--timeout", args.timeout)
        release = deployed(args)
        hooks = [hook for hook in release.get("hooks", []) if hook.get("kind") == "Job"]
        if not hooks or not all(hook.get("last_run", {}).get("phase") == "Succeeded" for hook in hooks):
            raise ValueError("The Helm release has no successful migration hook record.")
        print("Migration Job: Succeeded", flush=True)
        smoke(args, args.url or (url if args.profile != "local" else None))
        print(f"Published site configuration: {url}", flush=True)
    elif args.operation == "rollback":
        target = f"{args.context}/{args.namespace}/{args.release}/{args.revision}"
        if not args.revision or args.revision < 1 or args.confirm_target != target:
            parser.error("rollback requires --revision and --confirm-target equal to context/namespace/release/revision")
        if not args.schema_review or not args.schema_review.is_file() or not args.schema_review.read_text().strip():
            parser.error("rollback requires a written --schema-review")
        history = json.loads(helm(args, "history", args.release, "-o", "json", capture=True))
        if not any(entry["revision"] == args.revision and entry["status"] in ("superseded", "deployed") for entry in history):
            raise ValueError("Target revision is not a successful Helm deployment.")
        helm(args, "rollback", args.release, str(args.revision), "--wait", "--timeout", args.timeout)
        smoke(args, args.url)
    else:
        smoke(args, args.url)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError, yaml.YAMLError) as error:
        # Commands and exception URLs can include details controlled by the cluster or secrets.
        if isinstance(error, ValueError) and not isinstance(error, UnicodeError):
            print(f"ASPM: {error}", file=sys.stderr)
        else:
            print(f"ASPM: operation failed ({type(error).__name__}). See preceding diagnostic output.", file=sys.stderr)
        sys.exit(1)
