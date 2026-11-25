# Roles and capabilities

| Action | USER | EXPERT | SECOPS |
| --- | --- | --- | --- |
| Project, Repository or Commit visibility | Explicit Product grants | All | All |
| Historical observations and authorized downloads | Read | Read | Read |
| Generate a versioned report from a Commit | Denied | Allowed | Allowed |
| Live Finding browser and triage | Denied | View, bounded status edits and specified notes/actions | Allowed |
| Change Engagement policy | Denied | Denied | Allowed |
| Manage outbound webhooks | Denied | Denied | Allowed |
| Manage SSO Product mappings | Denied | Denied | Allowed |
| ASPM System Settings and Celery diagnostics | Denied | Denied | Allowed |
| Issue interactive API token for SSO account | Denied | Denied | Denied |

Role claim precedence is SecOps, Expert, then User. The User role and a matching issuer/opaque grant UUID are both required for Product access. Expert status PATCH allows the defined status fields only. Administrative capabilities are checked explicitly. Scope-limited managed sessions use an allowlist of reviewed routes and methods to keep legacy paths outside their permitted surface.

Existing local emergency and Django administration flows retain their native authority. The managed SSO account receives its ASPM permissions from the session and uses no Django superuser bit.
