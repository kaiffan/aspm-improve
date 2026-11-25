"""Generate a private, disposable TLS Keycloak realm and browser credentials."""
# ruff: noqa: INP001 -- standalone lab command
import argparse
import json
import secrets
import shutil
import subprocess
from pathlib import Path

TEST_GRANT = "30000000-0000-4000-8000-000000000001"
PAYMENTS_GRANT = "30000000-0000-4000-8000-000000000002"


def mapper(client, claim):
    return {
        "name": claim, "protocol": "openid-connect", "protocolMapper": "oidc-usermodel-client-role-mapper",
        "config": {
            "usermodel.clientRoleMapping.clientId": client, "claim.name": claim,
            "multivalued": "true", "jsonType.label": "String", "id.token.claim": "true",
            "access.token.claim": "false", "userinfo.token.claim": "false",
        },
    }


def realm(accounts, client_secret):
    return {
        "realm": "aspm-qualification", "enabled": True, "sslRequired": "all",
        "accessTokenLifespan": 300, "registrationAllowed": False, "resetPasswordAllowed": False,
        "roles": {"client": {
            "aspm": [{"name": role} for role in ("aspm-secops", "aspm-expert", "aspm-user")],
            "aspm-entitlements": [{"name": entitlement} for entitlement in (TEST_GRANT, PAYMENTS_GRANT)],
        }},
        "groups": [
            {"name": "devsecops-TEST-user", "clientRoles": {"aspm-entitlements": [TEST_GRANT]}},
            {"name": "devsecops-PAYMENTS-user", "clientRoles": {"aspm-entitlements": [PAYMENTS_GRANT]}},
        ],
        "clients": [
            {
                "clientId": "aspm", "enabled": True, "publicClient": False, "secret": client_secret,
                "standardFlowEnabled": True, "implicitFlowEnabled": False, "directAccessGrantsEnabled": False,
                "serviceAccountsEnabled": False,
                "redirectUris": ["https://localhost:48141/sso/callback"],
                "attributes": {"pkce.code.challenge.method": "S256", "post.logout.redirect.uris": "https://localhost:48141/login"},
                "protocolMappers": [mapper("aspm", "aspm_roles"), mapper("aspm-entitlements", "aspm_product_grants")],
            },
            {"clientId": "aspm-entitlements", "enabled": True, "bearerOnly": True, "standardFlowEnabled": False},
        ],
        "users": [
            {
                "username": name, "enabled": True, "firstName": "Qualification", "lastName": name,
                "email": f"{name}@example.test", "emailVerified": True,
                "credentials": [{"type": "password", "value": data["password"], "temporary": False}],
                "clientRoles": {"aspm": [data["role"]]}, "groups": data["groups"],
            }
            for name, data in accounts.items()
        ],
    }


def write_json(path, payload):
    path.touch(mode=0o600, exist_ok=False)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    state = parser.parse_args().directory
    state.mkdir(mode=0o700)
    accounts = {}
    for name, role, groups in (
        ("secops", "aspm-secops", []), ("expert", "aspm-expert", []),
        ("reader-test", "aspm-user", ["/devsecops-TEST-user"]),
        ("reader-payments", "aspm-user", ["/devsecops-PAYMENTS-user"]),
        ("reader-both", "aspm-user", ["/devsecops-TEST-user", "/devsecops-PAYMENTS-user"]),
        ("reader-none", "aspm-user", []),
    ):
        accounts[name] = {"password": secrets.token_urlsafe(24), "role": role, "groups": groups}
    client_secret = secrets.token_urlsafe(48)
    write_json(state / "accounts.json", {"accounts": accounts, "secret": client_secret, "admin": secrets.token_urlsafe(24)})
    write_json(state / "realm.json", realm(accounts, client_secret))
    openssl = shutil.which("openssl")
    if openssl is None:
        msg = "The openssl executable is required."
        raise RuntimeError(msg)
    for name in ("aspm-keycloak.test", "localhost"):
        subprocess.run([
            openssl, "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "3",
            "-subj", f"/CN={name}", "-addext", f"subjectAltName=DNS:{name}",
            "-keyout", str(state / f"{name}.key"), "-out", str(state / f"{name}.crt"),
        ], check=True, capture_output=True)
    # The container runtime needs read access to file mounts. The enclosing host
    # directory is private and never included in a release bundle.
    for name in ("realm.json", "aspm-keycloak.test.key"):
        (state / name).chmod(0o644)


if __name__ == "__main__":
    main()
