# ASPM final enterprise integration

**Release status HOLD.** The integration is available on `feature/aspm-final-enterprise-integration` for review and isolated qualification. The application and deployment sources are frozen at `7328daa441129bad49abd956e273e624362e655e`. This branch contains the verified hardening baseline on the fork's `dev` line.

The baseline already supplied the Product, Repository and Commit hierarchy, API-only ingestion, isolated ScanRun attempts, immutable observations, versioned reports, webhook events and Helm. This integration adds Product and Repository Engagement policies, verified Keycloak login, separated SecOps, Expert and User capabilities, Product grant mappings, and role-based pages for Projects, Reports, policy and access.

Six scanner fixture formats passed API acceptance, Celery processing, observation publication and generated export. The scanner compatibility matrix identifies the narrower scope of these results. Fortify and ffuf both passed independent fixture checks. The corporate abbreviation FF still requires identification and an export sample. [Scanner compatibility](SCANNER_COMPATIBILITY.md)

The local Keycloak realm uses synthetic users and groups. Browser and API evidence covers authentication, role-specific project visibility, original and generated downloads and Expert triage. The full suite, launch details, manifests, source hashes and remaining gates are recorded with the qualification evidence. [Test results](E2E_TEST_RESULTS.md) · [Release gates](RELEASE_GATE.md) · [Source provenance](raw/source-provenance.json)

## Dual workspace follow-up

The subsequent Classic and DevSecOps release candidate restores authorized Classic navigation and API workflows on the same Product and adds links between Tests and their Git evidence. Browser, API and backup/restore evidence for this candidate has its own regression matrix. The release status remains HOLD. [Architecture](DUAL_WORKSPACE_ARCHITECTURE.md) · [Regression matrix](CLASSIC_AND_DEVSECOPS_REGRESSION.md)
