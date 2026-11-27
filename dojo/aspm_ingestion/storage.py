import hashlib
import os
import re
import shutil
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory, TemporaryFile
from urllib.parse import quote

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.core.files import File
from django.core.files.storage import Storage
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from dojo.aspm_ingestion.models import StoredObject
from dojo.aspm_ingestion.object_store import (
    S3_ERRORS,
    ObjectUnavailableError,
    S3ObjectStore,
    check_digest,
    copy_and_hash,
    failure,
)
from dojo.aspm_observability import metrics as telemetry


def private_path(name):
    root = Path(settings.ASPM_ARTIFACT_ROOT).resolve()
    for public_root in (settings.MEDIA_ROOT, settings.STATIC_ROOT):
        if public_root and root.is_relative_to(Path(public_root).resolve()):
            msg = "ASPM evidence storage must be outside public media and static roots."
            raise SuspiciousFileOperation(msg)
    path = (root / name).resolve()
    if not path.is_relative_to(root) or path == root:
        raise SuspiciousFileOperation
    return path


def safe_name(name):
    # Names are display metadata only. Never use client filenames as storage keys.
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", name.replace("\\", "/").rsplit("/", 1)[-1])[:180] or "scan.bin"


def sync_directories(path):
    """Persist every new directory entry before committing its database reference."""
    root = Path(settings.ASPM_ARTIFACT_ROOT).resolve()
    directory = path.parent
    while directory.is_relative_to(root):
        directory.chmod(0o700)
        fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        if directory == root:
            break
        directory = directory.parent


class EvidenceUnavailable(APIException):
    status_code = 503
    default_detail = "Private evidence is temporarily unavailable or failed its integrity check."
    default_code = "evidence_unavailable"


def check_capacity(path):
    if shutil.disk_usage(path).free < settings.ASPM_STORAGE_MIN_FREE_BYTES:
        raise EvidenceUnavailable


def stored_object(store, name, digest, size, content_type):
    obj, _ = StoredObject.objects.get_or_create(
        name=name, defaults={
            "bucket": store.bucket, "object_key": store.key(name),
            "sha256": digest, "size": size, "content_type": content_type,
        },
    )
    store.address(obj)
    if (obj.backend, obj.sha256, obj.size, obj.content_type) != ("s3", digest, size, content_type) or obj.state == StoredObject.State.RETIRED:
        msg = "Object metadata conflicts with the existing registration."
        raise ObjectUnavailableError(msg)
    return obj


def stage_object(name, source, digest, size, content_type):
    store = S3ObjectStore()
    obj = stored_object(store, name, digest, size, content_type)
    if obj.state == StoredObject.State.READY:
        store.verify(obj)
        return obj
    try:
        store.put(obj, source)
    except S3_ERRORS as error:
        if telemetry.ENABLED:
            telemetry.STORAGE_FAILURES.labels("upload_write").inc()
        if isinstance(error, ObjectUnavailableError):
            raise
        raise failure(error) from error
    return obj


def publish_object(obj):
    if not StoredObject.objects.filter(pk=obj.pk, state__in=[StoredObject.State.STAGED, StoredObject.State.READY]).update(
        state=StoredObject.State.READY, version_id=obj.version_id, updated_at=timezone.now(),
    ):
        msg = "The object's staging lease was retired."
        raise ObjectUnavailableError(msg)


def open_object(name, digest=None, size=None):
    obj = StoredObject.objects.filter(name=name, backend="s3", state=StoredObject.State.READY).first()
    if obj is None:
        raise FileNotFoundError(name)
    if (digest is not None and obj.sha256 != digest) or (size is not None and obj.size != size):
        msg = "Object registration differs from the business record."
        raise ObjectUnavailableError(msg)
    return S3ObjectStore().open_verified(obj)


def verified_artifact(key, expected_sha256, expected_size=None):
    if not expected_sha256:
        raise ObjectUnavailableError
    if settings.ASPM_STORAGE_BACKEND == "s3":
        return open_object(f"private/{key}", expected_sha256, expected_size)
    source = private_path(key).open("rb")
    try:
        check_digest(source, expected_sha256, expected_size)
        source.seek(0)
    except BaseException:
        source.close()
        raise
    return source


def verified_open(key, expected_sha256, expected_size=None, *, report=False):
    try:
        return verified_artifact(key, expected_sha256, expected_size)
    except OSError as error:
        if report:
            telemetry.report_event("integrity_failed")
        raise EvidenceUnavailable from error


@contextmanager
def report_paths(json_key, html_key):
    if settings.ASPM_STORAGE_BACKEND == "s3":
        with TemporaryDirectory(dir=settings.ASPM_STORAGE_TEMP_DIR) as directory:
            yield Path(directory) / "report.json", Path(directory) / "report.html"
    else:
        json_path, html_path = private_path(json_key), private_path(html_key)
        json_path.parent.mkdir(mode=0o700, parents=True)
        try:
            yield json_path, html_path
        except BaseException:
            json_path.unlink(missing_ok=True)
            html_path.unlink(missing_ok=True)
            raise


def stage_report(key, path, content_type):
    with path.open("rb") as source:
        checksum, size = copy_and_hash(source)
        if settings.ASPM_STORAGE_BACKEND == "s3":
            return checksum, stage_object(f"private/{key}", source, checksum, size, content_type)
    sync_directories(path)
    return checksum, None


class BoundedTextOutput:
    def __init__(self, output):
        self.output = output
        self.bytes_written = 0
        self.last_capacity_check = 0

    def write(self, value):
        self.bytes_written += len(value.encode("utf-8"))
        if self.bytes_written > settings.ASPM_MAX_REPORT_BYTES:
            telemetry.report_event("size_limit")
            msg = "report_size_limit"
            raise ValueError(msg)
        if self.bytes_written - self.last_capacity_check >= 1024 * 1024:
            check_capacity(Path(self.output.name).parent)
            self.last_capacity_check = self.bytes_written
        return self.output.write(value)

    def flush(self):
        self.output.flush()

    def fileno(self):
        return self.output.fileno()


@contextmanager
def bounded_text_output(path):
    check_capacity(path.parent)
    with path.open("x", encoding="utf-8") as output:
        path.chmod(0o600)
        yield BoundedTextOutput(output)


def save_original(upload, *, expected_sha256=None, reuse=None):
    start = time.monotonic()
    key = f"originals/{uuid.uuid4().hex}/artifact"
    if settings.ASPM_STORAGE_BACKEND == "s3":
        check_capacity(settings.ASPM_STORAGE_TEMP_DIR)
        with TemporaryFile(dir=settings.ASPM_STORAGE_TEMP_DIR) as source:
            try:
                digest, size = copy_and_hash(upload, source, max_size=settings.ASPM_MAX_SCAN_BYTES)
            except ObjectUnavailableError as error:
                raise ValidationError({"file": "Scan exceeds the configured size limit."}) from error
            if not size:
                raise ValidationError({"file": "Empty reports are not accepted."})
            if expected_sha256 and digest != expected_sha256:
                raise ValidationError({"sha256": "The original does not match the supplied SHA256."})
            if reuse and (existing_key := reuse(digest, size)):
                return existing_key, digest, size, time.monotonic() - start, None
            obj = stage_object(f"private/{key}", source, digest, size, "application/octet-stream")
        return key, digest, size, time.monotonic() - start, obj
    return (*save_filesystem_original(upload, key, start), None)


def discard_original(key):
    if settings.ASPM_STORAGE_BACKEND == "filesystem":
        private_path(key).unlink(missing_ok=True)


def save_filesystem_original(upload, key, start):
    path = private_path(key)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=False)
    digest = hashlib.sha256()
    size = 0
    try:
        check_capacity(path.parent)
        with path.open("xb") as output:
            Path(path).chmod(0o600)
            for chunk in upload.chunks():
                size += len(chunk)
                if size > settings.ASPM_MAX_SCAN_BYTES:
                    raise ValidationError({"file": "Scan exceeds the configured size limit."})
                check_capacity(path.parent)
                digest.update(chunk)
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        if not size:
            raise ValidationError({"file": "Empty reports are not accepted."})
        # Persist the directory entry before acknowledging acceptance.
        sync_directories(path)
        return key, digest.hexdigest(), size, time.monotonic() - start
    except BaseException as error:
        if telemetry.ENABLED and isinstance(error, (EvidenceUnavailable, OSError)):
            telemetry.STORAGE_FAILURES.labels("upload_write").inc()
        path.unlink(missing_ok=True)
        raise


class PrivateMediaStorage(Storage):

    """Django FileField names remain local, authorized application URLs."""

    def _open(self, name, mode="rb"):
        if mode != "rb":
            raise NotImplementedError
        return File(open_object(f"media/{name}"), name)

    def _save(self, name, content):
        category = name.split("/", 1)[0]
        suffix = Path(name).suffix
        if not re.fullmatch(r"\.[A-Za-z0-9]{1,12}", suffix):
            suffix = ""
        name = f"{category}/{uuid.uuid4().hex}{suffix}"
        with TemporaryFile(dir=settings.ASPM_STORAGE_TEMP_DIR) as source:
            digest, size = copy_and_hash(content, source, max_size=settings.ASPM_MAX_MEDIA_BYTES)
            obj = stage_object(f"media/{name}", source, digest, size, "application/octet-stream")
        publish_object(obj)
        return name

    def exists(self, name):
        return StoredObject.objects.filter(name=f"media/{name}", state=StoredObject.State.READY).exists()

    def size(self, name):
        obj = StoredObject.objects.filter(name=f"media/{name}", state=StoredObject.State.READY).first()
        if obj is None:
            raise FileNotFoundError(name)
        return obj.size

    def url(self, name):
        return settings.MEDIA_URL.rstrip("/") + "/" + quote(name)

    def delete(self, name):
        if name:
            transaction.on_commit(lambda: retire_unreferenced_media(name), robust=True)


def retire_unreferenced_media(name):
    from dojo.models import FileUpload, Risk_Acceptance  # noqa: PLC0415 -- Django loads storage from settings

    if FileUpload.objects.filter(file=name).exists() or Risk_Acceptance.objects.filter(path=name).exists():
        return
    StoredObject.objects.filter(name=f"media/{name}", state=StoredObject.State.READY).update(
        state=StoredObject.State.RETIRED, updated_at=timezone.now(),
    )


def legacy_media_name(path):
    if not path or path == "none":
        return None
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            candidate = candidate.relative_to(Path(settings.MEDIA_ROOT))
        except ValueError as error:
            raise SuspiciousFileOperation from error
    if "\\" in path or ".." in candidate.parts or not candidate.parts or candidate.parts[0] not in {"threat", "selenium"}:
        raise SuspiciousFileOperation
    return candidate.as_posix()
