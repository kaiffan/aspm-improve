"""Copy or verify filesystem storage, or export and restore a consistent object inventory."""
import hashlib
import json
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from dojo.aspm_ingestion.models import GeneratedReport, ScanRun, StoredObject
from dojo.aspm_ingestion.object_store import S3ObjectStore, check_digest, copy_and_hash
from dojo.aspm_ingestion.storage import legacy_media_name, private_path, publish_object, stage_object
from dojo.models import Engagement, FileUpload, Risk_Acceptance


def references():
    for name, digest, size in ScanRun.objects.values_list("artifact_path", "artifact_sha256", "artifact_size").iterator(chunk_size=500):
        yield f"private/{name}", digest, size, "application/octet-stream"
    for json_name, html_name, checksums in GeneratedReport.objects.filter(status=ScanRun.Status.COMPLETED).values_list("json_path", "html_path", "checksums").iterator(chunk_size=500):
        yield f"private/{json_name}", checksums["json"], None, "application/json"
        yield f"private/{html_name}", checksums["html"], None, "text/html; charset=utf-8"
    for model, field in ((FileUpload, "file"), (Risk_Acceptance, "path"), (Engagement, "tmodel_path")):
        for stored_name in model.objects.exclude(**{f"{field}__in": ["", "none"]}).values_list(field, flat=True).iterator(chunk_size=500):
            name = legacy_media_name(stored_name) if field == "tmodel_path" else stored_name
            if name:
                yield f"media/{name}", None, None, "application/octet-stream"


@contextmanager
def filesystem_source(name):
    scope, logical = name.split("/", 1)
    if scope == "private":
        path = private_path(logical)
    else:
        root = Path(settings.MEDIA_ROOT).resolve()
        path = (root / logical).resolve()
        if not path.is_relative_to(root):
            msg = "Media path escapes the configured root."
            raise CommandError(msg)
    with path.open("rb") as source:
        yield source


def object_identity(name):
    return hashlib.sha256(name.encode()).hexdigest()


def manifest_rows(path):
    with path.open(encoding="utf-8") as manifest:
        yield from (json.loads(line) for line in manifest)


class Command(BaseCommand):
    help = "Plan, resume or verify RWX-to-S3 copy, or export/restore a frozen database's file references."

    def add_arguments(self, parser):
        parser.add_argument("operation", choices=["plan", "copy", "verify", "export", "restore"])
        parser.add_argument("--directory", type=Path)
        parser.add_argument("--writers-paused", action="store_true")
        parser.add_argument("--confirm-target")
        parser.add_argument("--expected-inventory-sha256")

    def handle(self, *args, **options):
        operation = options["operation"]
        if operation != "plan" and not options["writers_paused"]:
            msg = "Pause every ASPM writer before copying, validating, exporting or restoring."
            raise CommandError(msg)
        if operation in {"export", "restore"}:
            directory = options["directory"]
            if directory is None:
                msg = "Specify --directory for export and restore."
                raise CommandError(msg)
            if operation == "restore":
                self.restore(directory, options)
            else:
                self.export(directory)
            return
        store = None if operation == "plan" else S3ObjectStore()
        count = 0
        if operation == "copy" and settings.ASPM_STORAGE_BACKEND != "filesystem":
            msg = "Copy requires the existing filesystem profile and RWX mounts."
            raise CommandError(msg)
        for name, expected_hash, expected_size, content_type in references():
            if operation == "verify":
                obj = StoredObject.objects.get(name=name, state=StoredObject.State.READY)
                self.check_reference(obj, expected_hash, expected_size)
                store.verify(obj)
            else:
                with filesystem_source(name) as source:
                    digest, size = copy_and_hash(source, max_size=expected_size)
                    if (expected_hash and digest != expected_hash) or (expected_size is not None and size != expected_size):
                        msg = f"Source does not match database reference {object_identity(name)}."
                        raise CommandError(msg)
                    if operation == "copy":
                        obj = stage_object(name, source, digest, size, content_type)
                        publish_object(obj)
                    else:
                        self.stdout.write(json.dumps({"name": name, "sha256": digest, "size": size}, sort_keys=True))
            count += 1
        self.stderr.write(f"{operation}: verified {count} file references")

    def check_reference(self, obj, expected_hash, expected_size):
        if (expected_hash is not None and expected_hash != obj.sha256) or (expected_size is not None and expected_size != obj.size):
            msg = f"Storage does not match database reference {object_identity(obj.name)}."
            raise CommandError(msg)

    def export(self, directory):
        directory.mkdir(mode=0o700, exist_ok=False)
        store = S3ObjectStore() if settings.ASPM_STORAGE_BACKEND == "s3" else None
        blobs = directory / "objects"
        blobs.mkdir(mode=0o700)
        with (directory / "objects.jsonl").open("x", encoding="utf-8") as manifest:
            for name, expected_hash, expected_size, content_type in references():
                identifier = object_identity(name)
                destination = blobs / identifier
                if destination.exists():
                    continue
                if store:
                    obj = StoredObject.objects.get(name=name, state=StoredObject.State.READY)
                    self.check_reference(obj, expected_hash, expected_size)
                    with destination.open("xb") as target:
                        store.verify(obj, target)
                    digest, size = obj.sha256, obj.size
                    mapping = {"id": str(obj.pk), "bucket": obj.bucket, "key": obj.object_key, "version_id": obj.version_id}
                else:
                    with filesystem_source(name) as source, destination.open("xb") as target:
                        digest, size = copy_and_hash(source, target, max_size=expected_size)
                    if (expected_hash and digest != expected_hash) or (expected_size is not None and size != expected_size):
                        msg = f"Source does not match database reference {identifier}."
                        raise CommandError(msg)
                    mapping = None
                manifest.write(json.dumps({"name": name, "blob": identifier, "sha256": digest, "size": size, "content_type": content_type, "source": mapping}, sort_keys=True) + "\n")

    def restore(self, directory, options):
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            database, = cursor.fetchone()
        if database != options["confirm_target"] or settings.ASPM_STORAGE_BACKEND != "s3":
            msg = "Specify the isolated target database and use its S3 profile."
            raise CommandError(msg)
        manifest = directory / "objects.jsonl"
        if not options["expected_inventory_sha256"]:
            msg = "Specify the verified inventory SHA-256 from the recovery manifest."
            raise CommandError(msg)
        with manifest.open("rb") as source:
            check_digest(source, options["expected_inventory_sha256"], None)
        store = S3ObjectStore()
        for entry in manifest_rows(manifest):
            name = entry["name"]
            if entry["blob"] != object_identity(name):
                msg = "Object inventory contains an invalid blob identity."
                raise CommandError(msg)
            mapping = entry["source"]
            with (directory / "objects" / entry["blob"]).open("rb") as source:
                check_digest(source, entry["sha256"], entry["size"])
                if mapping is None:
                    obj = stage_object(name, source, entry["sha256"], entry["size"], entry["content_type"])
                    publish_object(obj)
                    continue
                self.restore_version(store, entry, mapping, source)
        self.handle(operation="verify", writers_paused=True)

    def restore_version(self, store, entry, mapping, source):
        obj = StoredObject.objects.get(pk=mapping["id"], name=entry["name"], state=StoredObject.State.READY)
        self.check_reference(obj, entry["sha256"], entry["size"])
        target_key = store.key(obj.name)
        previous = (obj.bucket, obj.object_key, obj.version_id)
        if previous[:2] == (store.bucket, target_key):
            store.verify(obj)
            return
        if previous != (mapping["bucket"], mapping["key"], mapping["version_id"]):
            msg = "Restored database differs from the source inventory."
            raise CommandError(msg)
        obj.bucket, obj.object_key, obj.version_id = store.bucket, target_key, ""
        store.put(obj, source)
        with transaction.atomic():
            if StoredObject.objects.filter(pk=obj.pk, bucket=previous[0], object_key=previous[1], version_id=previous[2]).update(
                bucket=obj.bucket, object_key=obj.object_key, version_id=obj.version_id, updated_at=timezone.now(),
            ) != 1:
                msg = "Storage mapping changed during the isolated restore."
                raise CommandError(msg)
