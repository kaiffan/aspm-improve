# Regression tests

The baseline focused run passed 108 tests. The initial complete run reproduced contract assertions that expected HTTP 400 for permission denial and a stale test database that contained duplicate Notification fixtures. Permission tests now assert HTTP 403 and keep their checks for unchanged data and access isolation. The performance guard still checks its original SQL limits. On a fresh local test database, 44 query-count and SLA tests passed for both the baseline and the candidate.

A later full run on a fresh database ran 8,888 tests and had one teardown error. PostgreSQL rejected the generic Django test flush because a retained compatibility table references Finding. The concurrent webhook test now uses the repository's committed fixtures and explicit cleanup. The qualification result for this fix is recorded in [RELEASE_GATE.md](RELEASE_GATE.md).

- Storage had returned HTTP 200 with corrupted artifact bytes. The candidate verifies SHA-256 before streaming and returns a sanitized HTTP 503 for missing or corrupt content. Tests cover both artifact and report downloads, and incomplete report publication when a quota trips.
- Legacy permission-denied views returned HTTP 400. Credential and object access regressions now check the HTTP 403 response with the existing authorization decisions intact.
- Browser analysis identified stale integration breadcrumbs, links distinguishable only by color, and keyboard-inaccessible evidence tables. The post-fix Playwright run exercised 66 page/viewport/theme combinations with no detected axe WCAG A/AA violations or page overflow.
- nginx attempted to create its FastCGI temp directory on a read-only filesystem. The chart sets FastCGI and SCGI temp paths under `/tmp`. The real nginx process passed `nginx -t`, login returned HTTP 200 and the readiness endpoint returned HTTP 200 using the corrected Helm commands.

The OpenAPI schema generated with `spectacular --fail-on-warn`. `makemigrations --check --dry-run` found no drift. Django system checks reported the local test image's existing missing frontend build directory warning. All 17 JavaScript tests passed.

The final run at `5133e155d102eb0f431560924ea129b2287319ff` completed 8,888 tests on a fresh database in 826.142 seconds. 8,335 passed and 553 inherited skips remained. The concurrent Finding webhook test passed with its committed fixtures and explicit cleanup. See [summary](raw/full-django-summary.json) and [compressed test output](raw/full-django-committed-fixtures.log.gz).
