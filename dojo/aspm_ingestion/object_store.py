"""Private S3 transport and verified, seekable temporary files."""
import hashlib
import logging
import re
from contextlib import closing
from functools import lru_cache
from tempfile import TemporaryFile
from urllib.parse import urlsplit

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError, HTTPClientError
from botocore.exceptions import ConnectionError as S3ConnectionError
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, SuspiciousFileOperation
from django.core.files.utils import validate_file_name

CHUNK_SIZE = 1024 * 1024
MIB = 1024 * 1024
S3_ERRORS = (BotoCoreError, ClientError, OSError)
logger = logging.getLogger(__name__)


class ObjectUnavailableError(OSError):

    """The configured object is inaccessible or its bytes fail verification."""


class ObjectTransportError(ObjectUnavailableError):
    pass


def failure(error):
    if isinstance(error, ObjectUnavailableError):
        return error
    if isinstance(error, ClientError):
        status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)
        if status == 429 or status >= 500 or error.response.get("Error", {}).get("Code") == "SlowDown":
            return ObjectTransportError("Private S3 temporarily unavailable.")
    if isinstance(error, (S3ConnectionError, HTTPClientError)):
        return ObjectTransportError("Private S3 temporarily unavailable.")
    return ObjectUnavailableError("Private S3 object is unavailable.")


def copy_and_hash(source, target=None, *, max_size=None):
    digest = hashlib.sha256()
    size = 0
    for chunk in iter(lambda: source.read(CHUNK_SIZE), b""):
        size += len(chunk)
        if max_size is not None and size > max_size:
            msg = "Object exceeds the configured size limit."
            raise ObjectUnavailableError(msg)
        digest.update(chunk)
        if target is not None:
            target.write(chunk)
    return digest.hexdigest(), size


def check_digest(source, sha256, size, target=None):
    actual_sha256, actual_size = copy_and_hash(source, target, max_size=size)
    if not sha256 or actual_sha256 != sha256 or (size is not None and actual_size != size):
        msg = "Object integrity check failed."
        raise ObjectUnavailableError(msg)
    if target is not None:
        target.seek(0)


@lru_cache(maxsize=4)
def s3_client(endpoint, region, ca, style, connect, read, attempts, access_key, secret_key, session_token):
    return boto3.session.Session().client(
        "s3", endpoint_url=endpoint, region_name=region, verify=ca or True,
        aws_access_key_id=access_key or None, aws_secret_access_key=secret_key or None,
        aws_session_token=session_token or None,
        config=Config(
            signature_version="s3v4", connect_timeout=connect, read_timeout=read,
            retries={"mode": "standard", "total_max_attempts": attempts},
            s3={"addressing_style": style}, request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    )


class S3ObjectStore:
    def __init__(self, *, quick_check=False):
        cfg = settings.ASPM_S3
        endpoint = urlsplit(cfg["endpoint"])
        if endpoint.scheme != "https" or not endpoint.hostname or endpoint.username is not None or endpoint.query or endpoint.fragment:
            msg = "Set an HTTPS ASPM S3 endpoint without credentials, query or fragment."
            raise ImproperlyConfigured(msg)
        self.bucket = cfg["bucket"]
        self.prefix = cfg["prefix"].strip("/")
        self.threshold = cfg["multipart_threshold_mib"] * MIB
        self.part_size = cfg["multipart_part_mib"] * MIB
        sse = cfg["encryption"]
        kms = cfg["kms_key_id"]
        if (
            not self.bucket or not re.fullmatch(r"[a-zA-Z0-9/_-]*", self.prefix)
            or not 5 * MIB <= self.part_size <= 64 * MIB
            or not self.part_size <= self.threshold <= 1024 * MIB
            or not 1 <= cfg["attempts"] <= 5
            or not 1 <= cfg["connect_timeout"] <= 60 or not 1 <= cfg["read_timeout"] <= 120
            or cfg["style"] not in {"auto", "path", "virtual"}
            or sse not in {"", "AES256", "aws:kms"} or (kms and sse != "aws:kms")
            or bool(cfg["access_key"]) != bool(cfg["secret_key"])
        ):
            msg = "Invalid ASPM S3 settings."
            raise ImproperlyConfigured(msg)
        self.encryption = {"ServerSideEncryption": sse} if sse else {}
        if kms:
            self.encryption["SSEKMSKeyId"] = kms
        limits = (1, 1, 1) if quick_check else (cfg["connect_timeout"], cfg["read_timeout"], cfg["attempts"])
        self.client = s3_client(
            cfg["endpoint"], cfg["region"], cfg["ca"], cfg["style"], *limits,
            cfg["access_key"], cfg["secret_key"], cfg["session_token"],
        )

    def key(self, name):
        validate_file_name(name, allow_relative_path=True)
        if "\\" in name:
            raise SuspiciousFileOperation
        scope, path = name.split("/", 1)
        if scope == "health":
            namespace = "temporary"
        elif scope == "private":
            category, path = path.split("/", 1)
            namespace = {"originals": "scanner-artifacts", "reports": "generated-reports"}[category]
        else:
            namespace = "evidence" if path.startswith(("risk/", "threat/")) else "attachments"
        return "/".join(part for part in (self.prefix, namespace, path) if part)

    def put(self, obj, source):
        address = {"Bucket": self.bucket, "Key": obj.object_key}
        headers = {
            "ContentType": obj.content_type,
            "Metadata": {"sha256": obj.sha256, "aspm-object": str(obj.pk)},
            **self.encryption,
        }
        source.seek(0)
        try:
            if obj.size < self.threshold:
                result = self.client.put_object(
                    **address, **headers, IfNoneMatch="*", ContentLength=obj.size, Body=source,
                )
            else:
                result = self.multipart(address, headers, source)
        except ClientError as error:
            if error.response["ResponseMetadata"]["HTTPStatusCode"] != 412:
                raise
            # A response can be lost after S3 commits a write. Resume only our own object.
            result = self.client.head_object(**address)
            if result.get("Metadata", {}).get("aspm-object") != str(obj.pk):
                msg = "Object key is already occupied."
                raise ObjectUnavailableError(msg) from error
        obj.version_id = result.get("VersionId") or ""
        self.verify(obj)

    def multipart(self, address, headers, source):
        upload_id = self.client.create_multipart_upload(**address, **headers)["UploadId"]
        upload = {**address, "UploadId": upload_id}
        parts = []
        try:
            for number, part in enumerate(iter(lambda: source.read(self.part_size), b""), 1):
                result = self.client.upload_part(**upload, PartNumber=number, Body=part)
                parts.append({"PartNumber": number, "ETag": result["ETag"]})
            return self.client.complete_multipart_upload(
                **upload, MultipartUpload={"Parts": parts}, IfNoneMatch="*",
            )
        except BaseException:
            try:
                self.client.abort_multipart_upload(**upload)
            except S3_ERRORS:
                logger.warning("ASPM multipart abort failed; storage lifecycle must expire incomplete uploads")
            raise

    def address(self, obj):
        if obj.bucket != self.bucket or obj.object_key != self.key(obj.name):
            msg = "Object location does not match the configured storage."
            raise ObjectUnavailableError(msg)
        address = {"Bucket": obj.bucket, "Key": obj.object_key}
        if obj.version_id:
            address["VersionId"] = obj.version_id
        return address

    def verify(self, obj, target=None):
        try:
            result = self.client.get_object(**self.address(obj))
            with closing(result["Body"]) as source:
                if result["ContentLength"] != obj.size or result.get("Metadata", {}).get("aspm-object") != str(obj.pk):
                    msg = "Object identity or size differs."
                    raise ObjectUnavailableError(msg)
                if obj.version_id and result.get("VersionId") != obj.version_id:
                    msg = "Object version differs."
                    raise ObjectUnavailableError(msg)
                check_digest(source, obj.sha256, obj.size, target)
        except (BotoCoreError, ClientError) as error:
            raise failure(error) from error

    def open_verified(self, obj):
        output = TemporaryFile(dir=settings.ASPM_STORAGE_TEMP_DIR)  # noqa: SIM115 -- lifetime belongs to the caller
        try:
            self.verify(obj, output)
        except BaseException:
            output.close()
            raise
        return output
