# Integration test results

Tested source candidate `7328daa441129bad49abd956e273e624362e655e`. Qualification used PostgreSQL and Celery on local ARM64 containers, Keycloak 26.6.4 with an isolated HTTPS realm, and Chromium. The runtime database and test databases used separate cache and broker namespaces. The workload used TEST with backend and frontend and PAYMENTS with payments-api, three seeded commits per repository, and six synthetic users.

## Functional and security results

| Check | Result |
| --- | --- |
| Trusted Keycloak authorization code exchange, PKCE and Product isolation | Six real login roles, with correct TEST, PAYMENTS, union and empty views |
| Engagement policy | SecOps configures Repository strategy in the live UI. PostgreSQL tests cover the five strategies, ten concurrent jobs, retry and cross-Product denial. |
| API-only scanner delivery | Six fixture formats complete through Celery and appear on the commit. A later Semgrep commit has independent history. |
| Report and artifact authorization | Same known identifier returns 200 for an authorized reader and 404 outside the Product scope. |
| Expert triage | Real Finding PATCH sets False Positive. The downloaded versioned report and historical observations keep their original contents. |
| Group revocation | New sign-in loses TEST immediately. Existing access ends after 118.968 seconds with a 120-second lab TTL. |
| Worker recovery | Run accepted while worker stopped, processed in one attempt after start, idempotent replay returned the same Run and Test. |
| Backup and restore | Relational hashes matched across eight tables. Verified all 27 scanner and generated report files. |
| Corporate UI | 12 Chromium layouts across desktop, tablet and mobile. A check confirmed the compiled stylesheet and loaded logo, bounded scrolling and at least 4.5:1 computed contrast for tested controls. |

[Browser assertions](raw/browser.json) · [Revocation](raw/keycloak-revocation.json) · [Worker recovery](raw/worker-recovery.json) · [Restored evidence](raw/local-restore.json)

## Browser captures

- SecOps policy on desktop. [Screenshot](raw/secops-engagement-1440-light.png)
- Expert Findings on tablet. [Screenshot](raw/expert-findings-820-light.png)
- User's project portfolio and immutable report on mobile dark. [Projects](raw/user-projects-390-dark.png) · [Report](raw/user-report-390-dark.png)

## Identity load and availability

Six parallel browser logins used separate cookie stores. The synthetic IdP returned the right Product portfolio for all six. With Keycloak stopped, a previously valid session still received HTTP 200 before expiry and HTTP 403 after 118.509 seconds. The lab IdP was restarted afterwards. [Parallel login results](raw/keycloak-concurrent.json) · [Outage behavior](raw/keycloak-outage.json)

## Independent checks

Full Django suite on the exact candidate completed in 424.3 seconds. 8,350 passed, 553 inherited skips, zero failures and zero errors. A preliminary run found a test route typo and query-count discrepancies while the runtime and test suite shared cache namespaces. The final run used a fresh database and isolated cache and broker namespaces. [Summary](raw/django-release-summary.json) · [Full log](raw/django-release.log.gz)

JavaScript theme, interaction and polling tests passed 17/17. The migration drift check reported no changes. The general v2 OpenAPI schema validated with the fail-on-warning option, and the dedicated endpoint returned the ASPM ingestion contract. The test image emitted the existing staticfiles.W004 warning about unmounted node_modules. The browser used compiled static assets from nginx. [JavaScript](raw/javascript.txt) · [Migration drift](raw/migration-check.txt) · [ASPM OpenAPI](raw/aspm-openapi.yaml)

Helm passed 13 chart tests, linting, profile rendering and strict manifest checks. The optional OIDC manifests also passed an OrbStack Kubernetes API server-side dry run. The node reports DiskPressure and NoSchedule, so this evidence does not include staging installation. [Chart checks](raw/helm-validation.txt) · [Kubernetes API](raw/kubernetes-server-dry-run.txt) · [Node conditions](raw/kubernetes-node-status.txt)
