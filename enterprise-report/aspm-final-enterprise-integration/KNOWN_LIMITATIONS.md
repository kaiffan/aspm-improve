# Open qualification items

- The corporate scanner called FF still needs the actual tool, version and export file.
- Corporate AD/LDAP federation, group sync and enterprise Keycloak failover have not been tested.
- Scoped routes for managed users are reviewed through the normal ASPM paths. Any newly installed plugin needs a separate authorization review.
- The native Linux/AMD64 build, Ryzen VM, million-Finding A/B and Acceptance A/B require the target environment and storage.
- Target Kubernetes install, upgrade and rollback are separate from rendered schema validation.
- WCAG 2.2 AA conformance and high-cardinality RBAC/overview testing remain target qualification items.

- The scanner diagnostics expose stable processing errors and last successful runs. The integration does not publish scanner-internal warning text or a structured warning taxonomy.
- Existing local Django account administration retains its break-glass permission model. SecOps administers the ASPM lists and Product mappings. Keycloak and directory administrators own IdP enrollment, client roles and credentials.
- The available OrbStack node is Ready and has a DiskPressure NoSchedule taint. Server dry run passed there. Target staging installation, upgrades and rollback need a schedulable cluster.
