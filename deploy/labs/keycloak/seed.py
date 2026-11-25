"""Seed the isolated runtime database. Execute inside a Django shell."""
# ruff: noqa: INP001, T201 -- local qualification outputs a private credential document
import json
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from dojo.aspm_access.models import SsoProductGrant
from dojo.aspm_ingestion.models import IngestionToken
from dojo.aspm_ingestion.services import issue_token
from dojo.product.models import Product
from dojo.product_type.models import Product_Type
from dojo.scm.models import Commit, Repository

if settings.DATABASES["default"]["NAME"] != "aspm_final_integration":
    msg = "Point this seed at the isolated aspm_final_integration runtime database."
    raise RuntimeError(msg)

product_type, _ = Product_Type.objects.get_or_create(name="ASPM qualification")
products = {}
for name, grant, repositories in (
    ("TEST", "30000000-0000-4000-8000-000000000001", ["backend", "frontend"]),
    ("PAYMENTS", "30000000-0000-4000-8000-000000000002", ["payments-api"]),
):
    product, _ = Product.objects.get_or_create(name=name, defaults={"description": "Synthetic ASPM lab", "prod_type": product_type})
    SsoProductGrant.objects.get_or_create(issuer=settings.ASPM_OIDC_ISSUER, group_id=grant, product=product)
    user, _ = get_user_model().objects.get_or_create(username=f"qualification-ci-{name.lower()}")
    user.set_unusable_password()
    user.save(update_fields=["password"])
    IngestionToken.objects.filter(user=user, product=product, label="Synthetic integration lab").update(revoked_at=timezone.now())
    _, raw = issue_token(
        user=user, product=product, scopes=["submit", "status", "read", "reports"],
        expires_at=timezone.now() + timedelta(hours=4), label="Synthetic integration lab",
    )
    repo_config = {}
    for name_in_repo in repositories:
        repository, _ = Repository.objects.get_or_create(product=product, url=f"https://git.example.test/qualification/{name_in_repo}")
        ids = {}
        for char in ("a", "b", "c"):
            commit, _ = Commit.objects.get_or_create(repository=repository, sha=char * 40, defaults={"branch": "main"})
            ids[char] = commit.pk
        repo_config[name_in_repo] = {"url": repository.url, "commits": ids}
    products[name] = {"id": product.pk, "token": raw, "repositories": repo_config}

print(json.dumps(products))
