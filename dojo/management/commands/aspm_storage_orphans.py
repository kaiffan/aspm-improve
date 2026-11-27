"""Report aged, unreferenced S3 registrations without deleting objects."""
from datetime import timedelta
from hashlib import sha256
from json import dumps
from pathlib import Path

from botocore.exceptions import ClientError
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from dojo.aspm_ingestion.models import GeneratedReport, ScanRun, StoredObject
from dojo.aspm_ingestion.object_store import S3ObjectStore
from dojo.models import Engagement, FileUpload, Risk_Acceptance


def is_referenced(name):
    scope, path = name.split("/", 1)
    if scope == "private":
        return (
            ScanRun.objects.filter(artifact_path=path).exists()
            or GeneratedReport.objects.filter(html_path=path).exists()
            or GeneratedReport.objects.filter(json_path=path).exists()
        )
    return (
        FileUpload.objects.filter(file=path).exists()
        or Risk_Acceptance.objects.filter(path=path).exists()
        or Engagement.objects.filter(tmodel_path__in=(path, str(Path(settings.MEDIA_ROOT) / path))).exists()
    )


class Command(BaseCommand):
    help = "Audit aged manufactured keys, optionally retiring unreferenced staging rows. It never deletes S3 versions."

    def add_arguments(self, parser):
        parser.add_argument("--grace-hours", type=int, default=72)
        parser.add_argument("--retire-staged", action="store_true")
        parser.add_argument("--writers-paused", action="store_true")

    def handle(self, *args, **options):
        if options["grace_hours"] < 24 or (options["retire_staged"] and not options["writers_paused"]):
            msg = "Use a grace period of at least 24 hours. Pause all writers before retiring staging rows."
            raise CommandError(msg)
        cutoff = timezone.now() - timedelta(hours=options["grace_hours"])
        store = S3ObjectStore()
        # Published but unreferenced media needs review because legacy string paths may be absolute.
        objects = StoredObject.objects.filter(updated_at__lt=cutoff, bucket=store.bucket).order_by("updated_at", "pk")
        for obj in objects.iterator(chunk_size=250):
            if is_referenced(obj.name):
                continue
            if options["retire_staged"] and obj.state == StoredObject.State.STAGED:
                with transaction.atomic():
                    changed = StoredObject.objects.filter(pk=obj.pk, state=obj.state, updated_at=obj.updated_at).update(state=StoredObject.State.RETIRED, updated_at=timezone.now())
                if changed:
                    obj.state = StoredObject.State.RETIRED
            version = self.matching_version(store, obj)
            self.stdout.write(dumps({
                "id": str(obj.pk), "name_sha256": sha256(obj.name.encode()).hexdigest(), "bucket": obj.bucket,
                "key": obj.object_key, "version_id": version, "state": obj.state, "created_at": obj.created_at.isoformat(),
            }, sort_keys=True))

    def matching_version(self, store, obj):
        try:
            result = store.client.head_object(**store.address(obj))
        except ClientError as error:
            if error.response["ResponseMetadata"]["HTTPStatusCode"] == 404:
                return None
            raise
        if result.get("Metadata", {}).get("aspm-object") == str(obj.pk):
            return result.get("VersionId") or ""
        return None
