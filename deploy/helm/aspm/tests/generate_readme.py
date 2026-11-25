# ruff: noqa: INP001 -- standalone CLI helpers invoke installed git/helm tools
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def rows(mapping, prefix=""):
    for key, value in mapping.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict) and value:
            yield from rows(value, path)
        else:
            yield f"| `{path}` | `{type(value).__name__}` | `{str(value).replace('|', '&#124;')}` |"


text = """# ASPM Helm chart

Unpublished release candidate. External PostgreSQL, separate Redis/Valkey broker/cache URLs,
private RWX evidence and shared media claims are required. No database or credential is generated.

Provision `aspm-runtime` with `django-secret-key`, `credential-aes-key`, `database-url`, `broker-url`,
`cache-url`; provision the PostgreSQL CA Secret and the two RWX PVCs before installation.
The database URL must identify the primary. Advisory locks require a direct or session-pooled connection.
Configure dependency CIDRs/selectors in `networkPolicy.egress`; the default permits only DNS.
Use verified immutable Django/nginx images from the same application source, pinned by digest in production.

```sh
helm lint deploy/helm/aspm
helm template aspm deploy/helm/aspm -f deploy/helm/aspm/values-staging.yaml
helm upgrade --install aspm deploy/helm/aspm -n aspm-staging --create-namespace \\
  -f /secure/aspm-staging.yaml --wait --timeout 35m
helm test aspm -n aspm-staging --logs
```

Set `tests.enabled=true` to install the optional Helm test hook. Migrations use a pre-install/upgrade
Job with a PostgreSQL lock. Web/worker/beat init containers block on the entire migration graph and
private-storage preflight. Jobs use only pre-existing Secrets and have no dependency on release ConfigMaps
or ServiceAccounts. Failed hooks remain for diagnosis. Beat has one replica, Recreate updates and database
session fencing. Ingestion and webhook outbox recovery share the existing periodic dispatcher; no second
scheduler is deployed. Worker SIGTERM grace is longer than the ingestion task limit.

Read [operations and gates](../../../enterprise-report/aspm-hardening/REPRODUCE.md), especially storage,
upgrade, backup/restore and NetworkPolicy limitations. Never infer Kubernetes readiness from rendering.
Read-only containers use explicit writable `/tmp`, runtime, evidence and media mounts. Root-squashed RWX
ownership must be provisioned for UID 1001/GID 1337. Non-root compatibility still needs CSI qualification.

This table is generated from values.yaml by tests/generate_readme.py.

| Key | Type | Default |
|---|---|---|
"""
(ROOT / "README.md").write_text(text + "\n".join(rows(yaml.safe_load((ROOT / "values.yaml").read_text()))) + "\n")
