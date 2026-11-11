# Regression and integration results

**100 tests executed; 92 passed, 8 skipped; zero failures/errors.** Repeated using the checked-out repository tests and a separate PostgreSQL database. No tests ran against the million-finding database. Four new guards failed on CURRENT before patches, then passed on FINAL. The fifth new test checks count sorting and real page boundaries.

New tests cover:

- Exact authorized Product counts, absent products, count/name ordering and pagination boundaries.
- Dashboard month cutoff, unknown severity and equivalent timezone-aware grouping.
- One daily aggregate query and the empty punchcard case.
- Simple Metrics exact opened/closed/severity totals and exclusion of false positives without loading Finding descriptions.

Preserved regression modules cover both Product aliases, CSV filters, unauthorized products, inherited access, no multiplied rows, standard/FAST pagination, custom ordering fallback, Product full/count/none, Test Jira groups and vulnerability references. Two actual linked vulnerability identifiers are returned in order in both representation branches and detail.

Modules:

```text
unittests.test_round4_performance
unittests.test_dashboard
unittests.test_api_finding_relation_filters
unittests.test_api_finding_filter_no_multiply
unittests.test_local_release_performance_checks
unittests.test_api_product_prefetch
unittests.test_apiv2_prefetch_test_finding_groups
unittests.test_authorization_queries
```

`test_local_release_performance_checks.py` was restored from the prior isolated runtime checks into Git, eliminating a private test-source dependency. Production source hashes match the tested commits. Django check, migration dry-run and OpenAPI --fail-on-warn succeeded. Test-environment warnings concern the pre-existing development encryption key and wildcard host configuration; they are not schema-generation failures. Ruff 0.17.4 passes for all five new production files and both new/restored test modules.

[Verification summary](test_verification.txt). Compared **70 full JSON pairs** and **28 HTML context pairs**: zero semantic failures. Dynamic HTML hashes are not claimed identical. HTTP observation counts/statuses are in `benchmark_results.json`; p99 is omitted below 300 successful samples.

## Skips inherited from the existing suite

- test_charts_as_user (unittests.test_dashboard.TestDashboard.test_charts_as_user) ... skipped 'Legacy auth re-baseline pending; same reason as test_counters_as_user.'
- test_counters_as_user (unittests.test_dashboard.TestDashboard.test_counters_as_user) ... skipped "Legacy authorization: dashboard counters use a per-user authorized queryset that under legacy gates on authorized_users membership. user1 is fixture-defined without authorized_users entries, and the _request helper's is_staff promotion isn't enough to make every dashboard counter match the original RBAC-tuned numbers (some of those numbers reflect role-specific filtering that legacy collapses). Re-baseline this test against legacy semantics in a follow-up."
- Superuser should get all endpoint statuses ... skipped 'Skipping because V3_FEATURE_LOCATIONS is enabled.'
- User with no permissions should not get test endpoint statuses ... skipped 'Skipping because V3_FEATURE_LOCATIONS is enabled.'
- User with product membership should get only that product's endpoint statuses ... skipped 'Skipping because V3_FEATURE_LOCATIONS is enabled.'
- Superuser should get all endpoints ... skipped 'Skipping because V3_FEATURE_LOCATIONS is enabled.'
- User with no permissions should not get test endpoints ... skipped 'Skipping because V3_FEATURE_LOCATIONS is enabled.'
- User with product membership should get only that product's endpoints ... skipped 'Skipping because V3_FEATURE_LOCATIONS is enabled.'

## Real import/reimport

The final write experiment uses three copies made after ANALYZE, one isolated Celery worker and an isolated broker/media. All 54 import/reimport POST return 201 with completed deduplication. Each of six sequences per build ends with primary 44 findings / 40 active and peer 40 findings / 40 duplicates. Request/response evidence and Location references exist, and API statistics match across builds. See `background_correctness.json` and `background_summary.json`.

The first write trial lacked planner statistics. It is preserved and excluded. A single control/loaded read pair per build does not establish a production read-impact SLA. Multiple real scanner formats, 20 million findings, networked HA PostgreSQL and browser JavaScript execution were not validated here. No production capacity claim is made.
