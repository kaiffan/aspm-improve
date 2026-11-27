"""Expose a private read-only metrics endpoint for a pod or singleton."""
import glob
import hmac
import json
import logging
import os
import re
import socket
import ssl
from copy import copy
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from time import monotonic

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest, multiprocess

LOGGER = logging.getLogger(__name__)


class Snapshot:
    def __init__(self, source, probe, interval):
        self.source = source
        self.probe = probe
        self.interval = interval
        self.updated = 0
        self.samples = ()
        Thread(target=self.run, daemon=True).start()

    def run(self):
        from django.db import connections  # noqa: PLC0415
        from time import sleep  # noqa: PLC0415

        while True:
            try:
                self.samples = tuple(self.probe())
                self.updated = monotonic()
            except Exception as error:
                self.updated = 0
                LOGGER.warning("Metrics probe %s failed (%s)", self.source, type(error).__name__)
            finally:
                connections.close_all()
            sleep(self.interval)

    def collect(self):
        from dojo.aspm_observability.snapshot import gauge  # noqa: PLC0415

        available = bool(self.updated and monotonic() - self.updated < 3 * self.interval)
        yield gauge("aspm_dependency_up", "Singleton probe returned fresh data", int(available), source=self.source)
        if available:
            yield from self.samples


def prune_web_gauges(path, stats):
    try:
        with socket.socket(socket.AF_UNIX) as client:
            client.settimeout(0.5)
            client.connect(stats)
            with client.makefile("rb") as stream:
                data = json.load(stream)
    except (OSError, ValueError):
        return
    live = {worker["pid"] for worker in data.get("workers", ())}
    for filename in glob.glob(f"{path}/gauge_live*_*.db"):
        if match := re.search(r"_(\d+)\.db$", filename):
            pid = int(match.group(1))
            if pid not in live:
                multiprocess.mark_process_dead(pid, path=path)


class SnapshotCollector:
    def __init__(self, probes):
        self.probes = probes

    def collect(self):
        families = {}
        for probe in self.probes:
            for metric in probe.collect():
                if metric.name in families:
                    families[metric.name].samples.extend(metric.samples)
                else:
                    family = copy(metric)
                    family.samples = list(metric.samples)
                    families[metric.name] = family
        return families.values()


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        self.request.settimeout(5)
        super().setup()

    def do_GET(self):
        if self.path != os.environ.get("ASPM_METRICS_PATH", "/metrics"):
            self.send_error(404)
            return
        if auth_file := os.environ.get("ASPM_METRICS_BEARER_FILE"):
            expected = b"Bearer " + Path(auth_file).read_bytes().strip()
            presented = self.headers.get("Authorization", "").encode()
            if expected == b"Bearer " or not hmac.compare_digest(expected, presented):
                self.send_error(401)
                return
        if stats := os.environ.get("ASPM_UWSGI_STATS"):
            prune_web_gauges(os.environ["PROMETHEUS_MULTIPROC_DIR"], stats)
        data = generate_latest(self.server.registry)
        self.send_response(200)
        self.send_header("Content-Type", CONTENT_TYPE_LATEST)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_args):
        pass


def main():
    registry = CollectorRegistry()
    if path := os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        multiprocess.MultiProcessCollector(registry, path)
    if os.environ.get("ASPM_METRICS_SINGLETON") == "true":
        import django  # noqa: PLC0415

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dojo.settings.settings")
        django.setup()
        from dojo.aspm_observability import snapshot  # noqa: PLC0415

        interval = max(30, int(os.environ.get("ASPM_METRICS_INTERVAL", "60")))
        probes = [
            Snapshot(source, probe, interval)
            for source, probe in (("database", snapshot.database), ("broker", snapshot.broker), ("storage", snapshot.storage))
        ]
        if os.environ.get("ASPM_METRICS_SECURITY") == "true":
            probes.append(Snapshot("security", snapshot.security, max(300, interval)))
        registry.register(SnapshotCollector(probes))
    server = HTTPServer(("0.0.0.0", 9108), Handler)
    server.socket.settimeout(5)
    server.registry = registry
    if cert := os.environ.get("ASPM_METRICS_CERT_FILE"):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(cert, os.environ["ASPM_METRICS_KEY_FILE"])
        server.socket = context.wrap_socket(server.socket, server_side=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
