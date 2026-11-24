import hashlib

from django.utils import timezone
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from dojo.aspm_ingestion.models import IngestionToken


class ServiceTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header or header[0].lower() != b"aspm":
            return None
        if len(header) != 2 or len(header[1]) > 200:
            msg = "Invalid ASPM credential."
            raise AuthenticationFailed(msg)
        digest = hashlib.sha256(header[1]).hexdigest()
        token = IngestionToken.objects.select_related("user", "repository").filter(
            digest=digest, revoked_at__isnull=True, expires_at__gt=timezone.now(), user__is_active=True,
            user__is_superuser=False, user__is_staff=False,
        ).first()
        if token is None or token.user.has_usable_password():
            msg = "Invalid or expired ASPM credential."
            raise AuthenticationFailed(msg)
        if token.repository_id and token.repository.product_id != token.product_id:
            msg = "Invalid ASPM scope."
            raise AuthenticationFailed(msg)
        return token.user, token

    def authenticate_header(self, request):
        return "ASPM"


class ServiceTokenScheme(OpenApiAuthenticationExtension):
    target_class = "dojo.aspm_ingestion.api.authentication.ServiceTokenAuthentication"
    name = "aspmServiceToken"

    def get_security_definition(self, auto_schema):
        return {"type": "apiKey", "in": "header", "name": "Authorization", "description": "ASPM <scoped service token>. Issued by a SecOps administrator; sessions and DefectDojo tokens cannot submit scans."}
