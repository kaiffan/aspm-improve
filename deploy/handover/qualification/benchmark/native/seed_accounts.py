"""Convert the frozen synthetic VUs into enrolled machine callers once before dumping."""
# ruff: noqa
import json
from datetime import timedelta
from pathlib import Path

from django.contrib.sessions.backends.db import SessionStore
from django.db import connection
from django.utils import timezone

from dojo.aspm_ingestion.services import issue_token
from dojo.models import Dojo_User, Product

assert __debug__
assert connection.settings_dict["NAME"]=="aspm_acceptance_seed"
home=Path("/acceptance-telemetry")
path=home/"accounts.json"
accounts=json.loads(path.read_text())
for row in accounts:
    user=Dojo_User.objects.get(pk=row["user_id"])
    assert not user.is_superuser and not user.is_staff and user.username.startswith("acceptance_vu_")
    user.set_unusable_password()
    user.save(update_fields=["password"])
    session=SessionStore()
    session["_auth_user_id"]=str(user.pk)
    session["_auth_user_backend"]="django.contrib.auth.backends.ModelBackend"
    session["_auth_user_hash"]=user.get_session_auth_hash()
    session.set_expiry(timezone.now()+timedelta(days=14))
    session.save()
    row["session"]=session.session_key
    row.pop("password",None)
    for pid in row["products"]:
        issue_token(user=user,product=Product.objects.get(pk=pid),scopes=["submit"],
                    expires_at=timezone.now()+timedelta(days=14),label="Qualification compatibility")
path.write_text(json.dumps(accounts))
path.chmod(0o600)
with (home/"identities.json").open("x") as f:
    Path(f.name).chmod(0o600)
    json.dump({"accounts":accounts},f)
