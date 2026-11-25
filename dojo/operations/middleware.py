import re
import uuid

from django.conf import settings

from dojo.operations.health import probe


class OperationsMiddleware:

    """Short circuit probes before auth, session and system-settings database access."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        prefix = "/" + settings.URL_PREFIX.strip("/") if settings.URL_PREFIX.strip("/") else ""
        if request.path in {prefix + "/health/live", prefix + "/health/ready", prefix + "/health/startup"}:
            return probe(request.path.rsplit("/", 1)[-1])
        supplied = request.headers.get("X-Correlation-ID", "")
        request.correlation_id = supplied if re.fullmatch(r"[a-zA-Z0-9_-]{8,64}", supplied) else uuid.uuid4().hex
        response = self.get_response(request)
        response["X-Correlation-ID"] = request.correlation_id
        return response
