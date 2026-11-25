# Negative authorization scenarios

`unittests.test_aspm_access` exercises no-group and union semantics, scoped Product and Commit lookup, artifact and report IDs, legacy Finding mutation denial, Expert status-only updates, managed token rejection, deactivation and session expiration. It uses signed fixture tokens for protocol errors and actual Django requests for the access rules.

The Chromium lab uses real Keycloak tokens from six synthetic identities. The TEST reader can access its Project, evidence and generated report. The PAYMENTS reader sees only PAYMENTS and receives HTTP 404 for TEST downloads. The union reader can access both, while the unassigned reader sees an empty portfolio. The Expert is denied System Settings. The SecOps user can change Engagement policy through a CSRF-protected form.

Production qualification also needs the organization's AD/LDAP group downgrade and incident-revocation runbook, plus authorization validation for any custom route or installed plugin.

In a separate live test, removing the TEST group immediately affected a new sign-in. An existing session lost access after 118.968 seconds with the local 120-second freshness setting. The harness restored the synthetic membership after verification. [Revocation result](raw/keycloak-revocation.json)
