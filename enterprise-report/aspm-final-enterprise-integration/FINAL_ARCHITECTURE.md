# Integrated architecture

The Product is the Project. Repository and Commit retain their existing identity constraints and primary keys. The ASPM API stores immutable evidence and enqueues the existing ingestion worker. The DefectDojo Test still owns live Findings. Report generation reads immutable observations and pins a set of runs and their generations.

```mermaid
flowchart LR
    CI["Scoped CI credential"] --> API["POST scans"]
    API --> Run["ScanRun + immutable artifact"]
    API --> Policy["Product / Repository policy"]
    Policy --> Engagement
    Run --> Job["Existing outbox and Celery worker"]
    Engagement --> Test["One Test per ScanRun"]
    Job --> Test
    Test --> Finding["Live Findings"]
    Test --> Observation["Historical observations"]
    Observation --> Report["Versioned HTML and JSON"]
    IdP["Keycloak HTTPS"] --> Session["Bounded ASPM session"]
    Session --> Grants["Permission and Product checks"]
    Grants --> Report
```

Managed bindings use Repository PK, strategy and scope. A nullable ScanRun-to-Engagement FK pins the selection before job dispatch. The database still requires legacy Tests to follow their commit-bound Engagement and verifies that new Tests use the pinned Engagement. The existing PostgreSQL finding-write and webhook event protocols remain in the import path.

The SSO database stores issuer and subject identity links and Product grant mappings. Verified role and group claims are held in server-side session data until the configured freshness deadline. Native Product memberships and machine ingestion tokens are independent.
