import hashlib
import os
import re
import time
import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from rest_framework.exceptions import ValidationError


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


def save_original(upload):
    start = time.monotonic()
    key = f"originals/{uuid.uuid4().hex}/artifact"
    path = private_path(key)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=False)
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("xb") as output:
            Path(path).chmod(0o600)
            for chunk in upload.chunks():
                size += len(chunk)
                if size > settings.ASPM_MAX_SCAN_BYTES:
                    raise ValidationError({"file": "Scan exceeds the configured size limit."})
                digest.update(chunk)
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        if not size:
            raise ValidationError({"file": "Empty reports are not accepted."})
        # Persist the directory entry before acknowledging acceptance.
        sync_directories(path)
        return key, digest.hexdigest(), size, time.monotonic() - start
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def verify_original(scan):
    digest = hashlib.sha256()
    size = 0
    with private_path(scan.artifact_path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    if size != scan.artifact_size or digest.hexdigest() != scan.artifact_sha256:
        msg = "artifact_integrity_failure"
        raise ValueError(msg)
