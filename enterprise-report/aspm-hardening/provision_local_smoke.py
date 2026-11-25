"""Create private scoped credentials on a specifically named disposable lab database."""
import json
import os
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.utils import timezone

from dojo.aspm_ingestion.services import issue_token
from dojo.models import Product, Product_Type
from dojo.scm.models import Repository


def provision():
    expected = os.environ["ASPM_QUALIFICATION_DB"]
    if not expected.startswith("aspm_hardening") or connection.settings_dict["NAME"] != expected:
        raise RuntimeError("Expected an explicitly named isolated hardening lab database")
    nonce = uuid.uuid4().hex[:12]
    with transaction.atomic():
        kind, _ = Product_Type.objects.get_or_create(name="ASPM hardening synthetic workload")
        product = Product.objects.create(name=f"ASPM qualification {nonce}", prod_type=kind, description="Isolated synthetic scan jobs")
        user = get_user_model().objects.create_user(username=f"qualification-{nonce}")
        fixtures = []
        for index in range(10):
            repository = Repository.objects.create(product=product, url=f"https://qualification.example.invalid/{nonce}/repo-{index}")
            _, token = issue_token(user=user, product=product, repository=repository, scopes=["submit", "status", "read", "reports"], expires_at=timezone.now() + timedelta(hours=2), label=f"local qualification repo {index}")
            fixtures.append({"repository_id": repository.pk, "token": token})
    return {"product_id": product.pk, "fixtures": fixtures}


if __name__ in {"__main__", "django.core.management.commands.shell"}:
    print(json.dumps(provision()))
