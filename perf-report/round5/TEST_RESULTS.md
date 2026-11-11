# Regression results

FINAL application: `c6a6144ed93b83adb1fd4ea9daa2c5e417ecea37`. Test source includes the final explicit hidden-Finding fixture and a frozen CaptureQueriesContext snapshot before subsequent HTTP calls.

* 104 tests: **96 pass, 8 skip, 0 fail**. [Final log](raw/tests_final.log).
* Four new performance guards fail on the actual Round4 image and pass on FINAL: [red log](raw/tests_red_final.log). Their failures concern the old SQL shapes/repeated aggregates; standard old API data was not presented as incorrect.
* Django check / migrations dry-run / schema generation exit 0. No changes detected. [Checks](raw/checks_final.log). Existing dojo.W003/W004 local-config warnings remain unchanged.
* Ruff passes on all six changed application files and the new test module.
* Full response verification: 196 pairs, 140 complete JSON hashes and 56 server-template context pairs, zero semantic/status/data mismatches. HTML hashes differ dynamically; templates were unchanged. [Details](compatibility.json).
* Default/full Product lists and detail: sorted complete active IDs, exact count, empty Product, multiple Products, metadata and visibility. count/none opt-ins checked separately.
* Dashboard: exact PK count despite two risk acceptances, duplicates excluded, hidden Finding absent from counters and API filter/detail. Three chart outputs checked against the former independent helpers, including UTC/New_York, cutoff/future/unknown severity.
* Previous suites cover Product prefetch, scoped Finding filters/CSV/custom order, standard/FAST pagination, multiple real vulnerability references, Jira/Test prefetch and authorization queries.
* Primary + standalone: 9,720 measured GETs, all 200, no stopped final series. Diagnostic GETs, warmups, expected-denial unit requests and exploratory/aborted candidates are excluded from that total.
* Source finding count, original-million IDs, full-row XOR, sum IDs and max_updated agree before/after and with preserved seed. [Before](fingerprint_before.json), [after](fingerprint_after.json).
* Corrected c25 RSS control samples all four real uWSGI workers; earlier sampler omission is explicitly documented in [RSS note](RSS_MEASUREMENT_NOTE.md).

## Skips

- test_charts_as_user (unittests.test_dashboard.TestDashboard.test_charts_as_user) ... skipped 'Legacy auth re-baseline pending; same reason as test_counters_as_user.'
- test_counters_as_user (unittests.test_dashboard.TestDashboard.test_counters_as_user) ... skipped "Legacy authorization: dashboard counters use a per-user authorized queryset that under legacy gates on authorized_users membership. user1 is fixture-defined without authorized_users entries, and the _request helper's is_staff promotion isn't enough to make every dashboard counter match the original RBAC-tuned numbers (some of those numbers reflect role-specific filtering that legacy collapses). Re-baseline this test against legacy semantics in a follow-up."
- Superuser should get all endpoint statuses ... skipped 'Skipping because V3_FEATURE_LOCATIONS is enabled.'
- User with no permissions should not get test endpoint statuses ... skipped 'Skipping because V3_FEATURE_LOCATIONS is enabled.'
- User with product membership should get only that product's endpoint statuses ... skipped 'Skipping because V3_FEATURE_LOCATIONS is enabled.'
- Superuser should get all endpoints ... skipped 'Skipping because V3_FEATURE_LOCATIONS is enabled.'
- User with no permissions should not get test endpoints ... skipped 'Skipping because V3_FEATURE_LOCATIONS is enabled.'
- User with product membership should get only that product's endpoints ... skipped 'Skipping because V3_FEATURE_LOCATIONS is enabled.'

## Limits

No new import/reimport or long production soak was executed in this read-focused round. Existing Round4 real import/deduplication evidence stays historical. No browser visual regression run was performed; server-rendered data and unchanged templates were checked. V3 paths skipped by the existing suite are not newly certified. Larger/representative scanner datasets, 25 independent humans with think time, and future external HA PostgreSQL remain untested.
