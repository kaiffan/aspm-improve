"""Create synthetic users and repositories in the dedicated load database."""
# ruff: noqa: INP001, S101, T201
import json
import os
import sys
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client
from django.utils import timezone

from dojo.aspm_ingestion.services import issue_token
from dojo.models import Product, Product_Type
from dojo.scm.models import Repository

if sys.flags.optimize or connection.settings_dict["NAME"] not in {"zf_load", "zf_native_load"}:
    msg = "Use a dedicated qualification database with assertions enabled."
    raise RuntimeError(msg)

nonce = uuid4().hex[:12]
group = Product_Type.objects.create(name=f"Qualification {nonce}")
product = Product.objects.create(name=f"Load {nonce}", description="Synthetic only", prod_type=group)
user = get_user_model().objects.create_user(username=f"zfq-{nonce}")
product.authorized_users.add(user.pk)
browser = Client()
browser.force_login(user)
_, token = issue_token(user=user, product=product, scopes=["submit", "status", "read", "reports"],
                       expires_at=timezone.now()+timedelta(hours=3), label=f"Qualification {nonce}")
repos = [
    Repository.objects.create(product=product, url=f"https://example.invalid/{nonce}/{index}").pk
    for index in range(10)
]
dest = Path(os.environ.get("ZF_LOAD_CREDENTIALS", "/tmp/zfq-load-private.json"))
with dest.open("x", encoding="utf-8") as stream:
    dest.chmod(0o600)
    json.dump({"nonce":nonce,"product":product.pk,"repositories":repos,"token":token,
               "session":browser.cookies["sessionid"].value},stream)
