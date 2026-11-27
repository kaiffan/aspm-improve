import time

from django.conf import settings
from django.core.files.uploadhandler import FileUploadHandler, StopUpload
from django.db import connection
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.exceptions import Throttled, ValidationError
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from dojo.aspm_ingestion.api.authentication import ServiceTokenAuthentication
from dojo.aspm_ingestion.api.serializer import (
    FinalizeSerializer,
    ReportRequestSerializer,
    ReportSerializer,
    ScanRunSerializer,
    ScanSetSerializer,
    ScanUploadSerializer,
)
from dojo.aspm_ingestion.models import GeneratedReport, IngestionToken, ScanRun
from dojo.aspm_ingestion.services import accept_scan, finalize_commit, request_report, require_scope, retry_scan
from dojo.aspm_ingestion.storage import EvidenceUnavailable, verified_open
from dojo.aspm_observability import metrics as telemetry
from dojo.product.queries import get_authorized_products
from dojo.scm.api.serializer import CommitSerializer, RepositorySerializer
from dojo.scm.models import Commit, Repository


class BoundedUploadHandler(FileUploadHandler):
    def __init__(self, request):
        super().__init__(request)
        self.received = 0

    def receive_data_chunk(self, raw_data, start):
        self.received += len(raw_data)
        if self.received > settings.ASPM_MAX_SCAN_BYTES:
            raise StopUpload(connection_reset=True)
        return raw_data

    def file_complete(self, file_size):
        return None


class AspmView(APIView):
    authentication_classes = (ServiceTokenAuthentication, *api_settings.DEFAULT_AUTHENTICATION_CLASSES)
    permission_classes = (IsAuthenticated,)
    parser_classes = (JSONParser,)
    http_method_names = ("get", "post", "head", "options")

    def after(self, request, *, uuid=False):
        field = serializers.UUIDField() if uuid else serializers.IntegerField(min_value=0, max_value=2**63 - 1)
        return field.run_validation(request.query_params["after"]) if request.query_params.get("after") else None

    def initial(self, request, *args, **kwargs):
        if not settings.ASPM_INGESTION_ENABLED:
            from django.http import Http404  # noqa: PLC0415 -- optional feature
            raise Http404
        super().initial(request, *args, **kwargs)
        if isinstance(request.auth, IngestionToken):
            # PostgreSQL UPSERT serializes an exact fixed-minute limiter across app replicas.
            # It runs before DRF parses the multipart body. No request or credential is logged.
            bucket_minute = int(time.time()) // 60
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO aspm_ingestion_rate (token_id, bucket_minute, requests) VALUES (%s, %s, 1) "
                    "ON CONFLICT (token_id) DO UPDATE SET bucket_minute=EXCLUDED.bucket_minute, "
                    "requests=CASE WHEN aspm_ingestion_rate.bucket_minute=EXCLUDED.bucket_minute THEN aspm_ingestion_rate.requests+1 ELSE 1 END RETURNING requests",
                    [request.auth.pk, bucket_minute],
                )
                count = cursor.fetchone()[0]
            if count > settings.ASPM_TOKEN_RATE_PER_MINUTE:
                raise Throttled(wait=60)

    def repositories(self, request):
        if isinstance(request.auth, IngestionToken):
            require_scope(request.auth, "read")
            qs = Repository.objects.filter(product_id=request.auth.product_id)
            return qs.filter(pk=request.auth.repository_id) if request.auth.repository_id else qs
        return Repository.objects.filter(product__in=get_authorized_products("view", user=request.user))

    def commit(self, request, pk):
        return get_object_or_404(Commit.objects.select_related("repository__product").filter(repository__in=self.repositories(request)), pk=pk)

    def scan(self, request, pk):
        qs = ScanRun.objects.select_related("commit__repository")
        if isinstance(request.auth, IngestionToken):
            require_scope(request.auth, "status")
            qs = qs.filter(product_id=request.auth.product_id, submitted_by_id=request.user.pk)
            if request.auth.repository_id:
                qs = qs.filter(commit__repository_id=request.auth.repository_id)
        else:
            qs = qs.filter(commit__repository__in=self.repositories(request))
        return get_object_or_404(qs, pk=pk)


class ScanUploadView(AspmView):
    parser_classes = (MultiPartParser,)

    def initialize_request(self, request, *args, **kwargs):
        request.upload_handlers.insert(0, BoundedUploadHandler(request))
        return super().initialize_request(request, *args, **kwargs)

    @extend_schema(auth=[{"aspmServiceToken": []}], parameters=[OpenApiParameter("Idempotency-Key", str, location=OpenApiParameter.HEADER)], request=ScanUploadSerializer, responses={202: ScanRunSerializer, 200: ScanRunSerializer}, tags=["ASPM ingestion"])
    def post(self, request):
        start = time.monotonic()
        require_scope(request.auth, "submit")
        if int(request.META.get("CONTENT_LENGTH") or 0) > settings.ASPM_MAX_SCAN_BYTES + 65536:
            msg = "Request exceeds the configured size limit."
            raise ValidationError(msg)
        data = {key: request.data[key] for key in request.data}
        if header_key := request.headers.get("Idempotency-Key"):
            if data.get("idempotency_key") and data["idempotency_key"] != header_key:
                msg = "Idempotency-Key header differs from form field."
                raise ValidationError(msg)
            data["idempotency_key"] = header_key
        serializer = ScanUploadSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        upload = values.pop("file")
        scan, created = accept_scan(request.auth, values, upload, correlation_id=getattr(request, "correlation_id", None))
        payload = ScanRunSerializer(scan).data
        payload["acceptance_seconds"] = time.monotonic() - start
        return Response(payload, status=202 if created else 200)


class ScanDetailView(AspmView):
    @extend_schema(responses=ScanRunSerializer, tags=["ASPM ingestion"])
    def get(self, request, pk):
        return Response(ScanRunSerializer(self.scan(request, pk)).data)


class ScanRetryView(AspmView):
    @extend_schema(auth=[{"aspmServiceToken": []}], request=None, responses={202: ScanRunSerializer}, tags=["ASPM ingestion"])
    def post(self, request, pk):
        require_scope(request.auth, "submit")
        return Response(ScanRunSerializer(retry_scan(self.scan(request, pk))).data, status=202)


class ArtifactDownloadView(AspmView):
    @extend_schema(responses={(200, "application/octet-stream"): bytes}, tags=["ASPM ingestion"])
    def get(self, request, pk):
        scan = self.scan(request, pk)
        response = FileResponse(verified_open(scan.artifact_path, scan.artifact_sha256, scan.artifact_size), as_attachment=True, filename=scan.original_name, content_type="application/octet-stream")
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        response["Content-Security-Policy"] = "sandbox; default-src 'none'"
        return response


class ProjectRepositoriesView(AspmView):
    @extend_schema(parameters=[OpenApiParameter("after", int, description="Last repository ID; at most 100 rows per page.")], responses=RepositorySerializer(many=True), tags=["ASPM ingestion"])
    def get(self, request, pk):
        return Response(RepositorySerializer(self.repositories(request).filter(product_id=pk, pk__gt=self.after(request) or 0).order_by("pk")[:100], many=True).data)


class RepositoryCommitsView(AspmView):
    @extend_schema(parameters=[OpenApiParameter("after", int, description="Last commit ID; at most 100 rows per page.")], responses=CommitSerializer(many=True), tags=["ASPM ingestion"])
    def get(self, request, pk):
        repository = get_object_or_404(self.repositories(request), pk=pk)
        return Response(CommitSerializer(repository.commits.filter(pk__gt=self.after(request) or 0).order_by("pk")[:100], many=True).data)


class CommitScansView(AspmView):
    @extend_schema(parameters=[OpenApiParameter("after", str, description="Last ScanRun UUID; at most 100 rows per page.")], responses=ScanRunSerializer(many=True), tags=["ASPM ingestion"])
    def get(self, request, pk):
        scans = self.commit(request, pk).scan_runs.order_by("pk")
        if after := self.after(request, uuid=True):
            scans = scans.filter(pk__gt=after)
        if isinstance(request.auth, IngestionToken):
            scans = scans.filter(submitted_by=request.user)
        return Response(ScanRunSerializer(scans[:100], many=True).data)


class FinalizeView(AspmView):
    @extend_schema(auth=[{"aspmServiceToken": []}], request=FinalizeSerializer, deprecated=True, description="Optional legacy operation to pin an explicit set; never required for visibility or export.", responses={201: ScanSetSerializer}, tags=["ASPM ingestion"])
    def post(self, request, pk):
        require_scope(request.auth, "finalize")
        serializer = FinalizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = finalize_commit(self.commit(request, pk), serializer.validated_data["expected_scanners"], scan_ids=serializer.validated_data.get("scan_ids"))
        return Response(ScanSetSerializer(result).data, status=201)


class CommitReportsView(AspmView):
    @extend_schema(auth=[{"aspmServiceToken": []}], request=ReportRequestSerializer, responses={202: ReportSerializer}, tags=["ASPM ingestion"])
    def post(self, request, pk):
        require_scope(request.auth, "reports")
        serializer = ReportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = request_report(self.commit(request, pk), **serializer.validated_data)
        return Response(ReportSerializer(report).data, status=202)

    @extend_schema(parameters=[OpenApiParameter("after", int, description="Last report version; at most 100 rows per page.")], responses=ReportSerializer(many=True), tags=["ASPM ingestion"])
    def get(self, request, pk):
        return Response(ReportSerializer(self.commit(request, pk).aspm_reports.filter(version__gt=self.after(request) or 0).order_by("version")[:100], many=True).data)


class ReportDownloadView(AspmView):
    def perform_content_negotiation(self, request, force=False):  # noqa: FBT002 -- DRF override signature
        # Here format selects the downloaded artifact, not a DRF response renderer.
        renderer = self.get_renderers()[0]
        return renderer, renderer.media_type

    @extend_schema(parameters=[OpenApiParameter("format", str, enum=["html", "json"])], responses={(200, "text/html"): bytes, (200, "application/json"): bytes}, tags=["ASPM ingestion"])
    def get(self, request, pk):
        report = get_object_or_404(GeneratedReport.objects.filter(commit__repository__in=self.repositories(request)), pk=pk, status=ScanRun.Status.COMPLETED)
        output_format = request.query_params.get("format", "html")
        if output_format not in {"html", "json"}:
            msg = "format must be html or json."
            raise ValidationError(msg)
        key = report.html_path if output_format == "html" else report.json_path
        try:
            artifact = verified_open(key, report.checksums.get(output_format), report=True)
        except EvidenceUnavailable:
            telemetry.report_event("download_failed")
            if telemetry.ENABLED:
                telemetry.STORAGE_FAILURES.labels("report_read").inc()
            raise
        response = FileResponse(artifact, as_attachment=True, filename=f"aspm-{report.commit_id}-v{report.version}.{output_format}", content_type="text/html; charset=utf-8" if output_format == "html" else "application/json")
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        response["Content-Security-Policy"] = "sandbox; default-src 'none'"
        return response
