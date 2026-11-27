"""Exercise the delivery publisher without contacting a registry."""
# ruff: noqa: INP001 -- tests for a standalone delivery script

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("publish-images.sh")
APP_SHA = "1" * 40
MONITORING_SHA = "2" * 40
DJANGO_DIGEST = "sha256:" + "3" * 64
NGINX_DIGEST = "sha256:" + "4" * 64

DOCKER = """#!/usr/bin/env python3
import os
import sys

command = sys.argv[1:]
image = next(arg for arg in command if arg.startswith("registry.example.com/"))
django = "/django" in image
digest = "sha256:" + ("3" if django else "4") * 64
revision = os.environ["TEST_IMAGE_REVISION"]

if command[:2] == ["image", "inspect"]:
    expected = f":{revision[:12]}-amd64"
    assert image.endswith(expected) or image.endswith("@" + digest), image
    print(f"image-{django} linux/amd64 {revision}")
elif command[:2] == ["buildx", "imagetools"]:
    print(digest)
elif command[0] not in ("push", "pull"):
    raise SystemExit(f"Unexpected docker command: {command}")
"""


class PublishImagesTests(unittest.TestCase):
    def publish(self, manifest, revision, *options):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            script = shutil.copy2(SCRIPT, root / "scripts")
            (root / "DELIVERY_MANIFEST.json").write_text(json.dumps(manifest))
            docker = root / "docker"
            docker.write_text(DOCKER)
            docker.chmod(0o755)
            output = root / "images.yaml"
            result = subprocess.run(
                [shutil.which("bash"), script, *options, "linux/amd64", "registry.example.com/platform/aspm", output],
                env={**os.environ, "PATH": f"{root}{os.pathsep}{os.environ['PATH']}", "TEST_IMAGE_REVISION": revision},
                check=False,
                capture_output=True,
                text=True,
            )
            return result, output.read_text() if output.is_file() else ""

    def test_current_package_uses_application_revision(self):
        result, values = self.publish({"application_sha": APP_SHA}, APP_SHA)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"digest: {DJANGO_DIGEST}", values)
        self.assertIn(f"digest: {NGINX_DIGEST}", values)
        self.assertIn(f'DD_ASPM_GIT_SHA: "{APP_SHA}"', values)

    def test_explicit_monitoring_revision_remains_supported(self):
        manifest = {"application_sha": APP_SHA, "monitoring": {"source_sha": MONITORING_SHA}}
        result, values = self.publish(manifest, MONITORING_SHA, "--monitoring")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f'DD_ASPM_GIT_SHA: "{MONITORING_SHA}"', values)

    def test_missing_monitoring_source_fails_before_creating_values(self):
        result, values = self.publish({"application_sha": APP_SHA}, APP_SHA, "--monitoring")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no monitoring source revision", result.stderr)
        self.assertEqual(values, "")


if __name__ == "__main__":
    unittest.main()
