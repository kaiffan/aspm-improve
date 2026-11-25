"""Create disposable users and a scoped CI token on the explicitly named ASPM lab DB."""
# ruff: noqa: INP001 -- standalone CLI fixture for manage.py shell
import json
import secrets
import sys
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.utils import timezone

from dojo.aspm_ingestion.services import issue_token
from dojo.models import Product, Product_Type
from dojo.scm.models import Repository


def provision():
    if connection.settings_dict["NAME"] not in {"aspm_lab", "aspm_hardening"}:
        message = "This fixture requires the isolated ASPM lab database"
        raise RuntimeError(message)

    suffix = secrets.token_hex(5)
    User = get_user_model()
    with transaction.atomic():
        product_type, _ = Product_Type.objects.get_or_create(name="Webhook qualification lab")
        product = Product.objects.create(name=f"Webhook lab {suffix}", description="Synthetic qualification only", prod_type=product_type)
        repo = Repository.objects.create(product=product, url=f"https://qualification.example.invalid/{suffix}/scan")
        admin_password, viewer_password = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        admin = User.objects.create_superuser(username=f"webhook-lab-admin-{suffix}", email=f"admin-{suffix}@example.invalid", password=admin_password)
        viewer = User.objects.create_user(username=f"webhook-lab-viewer-{suffix}", password=viewer_password)
        product.authorized_users.add(viewer.pk)
        service = User.objects.create_user(username=f"webhook-lab-ci-{suffix}")
        _, raw_token = issue_token(user=service, product=product, repository=repo, scopes=["submit", "status"], expires_at=timezone.now() + timedelta(hours=2), label="Webhook lab CI")
    return {
        "product_id": product.pk, "repository_id": repo.pk, "suffix": suffix,
        "admin": {"username": admin.username, "password": admin_password},
        "viewer": {"username": viewer.username, "password": viewer_password},
        "token": raw_token,
    }


if __name__ == "__main__":
    json.dump(provision(), sys.stdout)
    sys.stdout.write("\n")
