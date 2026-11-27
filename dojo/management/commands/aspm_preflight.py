import hashlib
import os
import pathlib
import shutil
import time
import uuid
from io import BytesIO
from types import SimpleNamespace

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from dojo.aspm_ingestion.object_store import S3_ERRORS, S3ObjectStore
from dojo.aspm_ingestion.storage import private_path, sync_directories


def schema_ready():
    executor = MigrationExecutor(connection)
    return not executor.migration_plan(executor.loader.graph.leaf_nodes())


def storage_ready(*, writable=True):
    if settings.ASPM_STORAGE_BACKEND == "s3":
        probe = b"aspm-private-storage-probe-v1"
        store = S3ObjectStore(quick_check=not writable)
        name = "health/private-storage-v1"
        key = store.key(name)
        obj = SimpleNamespace(
            pk=uuid.uuid5(uuid.NAMESPACE_URL, f"{store.bucket}/{key}"), name=name,
            bucket=store.bucket, object_key=key, version_id="", size=len(probe),
            sha256=hashlib.sha256(probe).hexdigest(), content_type="application/octet-stream",
        )
        try:
            if writable:
                store.put(obj, BytesIO(probe))
            else:
                store.verify(obj)
        except S3_ERRORS as error:
            msg = "Private S3 storage is unavailable."
            raise CommandError(msg) from error
        return

    root = private_path("preflight")
    if not writable:
        if not root.is_dir() or not os.access(root, os.R_OK | os.W_OK) or shutil.disk_usage(root).free < settings.ASPM_STORAGE_MIN_FREE_BYTES:
            msg = "Private filesystem is unavailable."
            raise CommandError(msg)
        return
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if shutil.disk_usage(root).free < settings.ASPM_STORAGE_MIN_FREE_BYTES:
        msg = "Private evidence storage is below the configured capacity reserve."
        raise CommandError(msg)
    name = root / uuid.uuid4().hex
    published = name.with_suffix(".published")
    try:
        with name.open("xb") as output:
            pathlib.Path(name).chmod(0o600)
            output.write(b"aspm-private-storage-probe")
            output.flush()
            os.fsync(output.fileno())
        name.rename(published)
        sync_directories(published)
        if published.read_bytes() != b"aspm-private-storage-probe":
            msg = "Private evidence storage read-after-write failed."
            raise CommandError(msg)
    finally:
        name.unlink(missing_ok=True)
        published.unlink(missing_ok=True)


class Command(BaseCommand):
    help = "Fence application startup on the full migration graph and writable private evidence storage."

    def add_arguments(self, parser):
        parser.add_argument("--wait-seconds", type=int, default=0)

    def handle(self, *args, **options):
        deadline = time.monotonic() + options["wait_seconds"]
        while True:
            try:
                if schema_ready():
                    break
            except Exception:
                connection.close()
            if time.monotonic() >= deadline:
                msg = "Database is unavailable or schema migration is incomplete."
                raise CommandError(msg)
            time.sleep(1)
        storage_ready()
        self.stdout.write("ASPM schema and private storage preflight passed")
