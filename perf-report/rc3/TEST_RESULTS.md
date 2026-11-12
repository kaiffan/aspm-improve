# Accepted-candidate validation

Sanctioned `./run-unittest.sh --test-case unittests`, offline test PostgreSQL and
read-only source mounts, runtime source `ccfd52d372695176485e65000b4270e01d7dfb1b`:
**8706 run; 8153 passed; 0 failures; 0 errors;
553 skipped**. Full method outcomes/skip reasons: `raw/full-final-tests.json`.
JavaScript: 12/12 passed, 0 failures/skips (`raw/javascript-tests.log`). Frontend
packages define build scripts but no additional test command.

Both original import errors are reproduced with full tracebacks in
`raw/discovery-red.log`, and resolved by restoring actual upstream implementations,
not test exclusions/stubs. `raw/discovery-green.log` proves full module loading.
The first post-blocker suite exposed one separate concurrent-index fixture timing
race; its traceback and the failed summary are retained. The fixture now releases
the snapshot on observed polling, with unchanged production migration code.

| Guard/module | Passed methods in full suite |
| --- | --- |
| test_round4_performance | 5 |
| test_round5_performance | 4 |
| test_api_finding_relation_filters | 10 |
| test_api_finding_filter_no_multiply | 6 |
| test_local_release_performance_checks | 3 |
| test_api_product_prefetch | 6 |
| test_apiv2_prefetch_test_finding_groups | 3 |
| test_rc2_product_filters | 6 |
| test_ui_pagination_hardening | 9 |
| test_rc3_finding_scope | 6 |
| test_rc3_finding_page | 7 |
| test_ticket_comments | 21 |
| test_trufflehog_parser | 8 |


This covers retained Round 1–5 API/query/prefetch/pagination guards, RC2 filters,
Product/Finding permissions, import/reimport, dedup, evidence and reports. The new
scope guard fails on RC2 and passes on RC3; the related-sort and to-many-filter
page guards first reproduced changed page rows and pass after conservative
fallbacks. Their original failures and focused green outcomes are retained.
Ruff 0.16.10 passes changed production/tests; check/migration dry-run/schema
management results are in `raw/management-checks.json`. No new migration.

## Real API, browser and writes

* 108 before/after profile pairs: 76 complete JSON hashes and
  32 meaningful template context comparisons; mismatches=0, including
  expected restricted users/notes 403 results.
* Browser: 50 page/theme/viewport states,
  12 functional checks; failures=0. Real Playwright/Chromium,
  axe, Light/Dark/System, keyboard/sidebar, Select2, selection and rapid navigation.
  Screenshots live in `screenshots/`. No CSS/SVG/palette/navigation rewrite.
* Server pagination matrix: 140 checks, failures=0: first/next/prev/
  last, malformed/negative/huge page, page sizes, filters/sort/empty results,
  Test prefix and admin/restricted identities.
* Real ZAP import/reimport/duplicate-peer: three 201 responses with completed
  dedup. Primary 44 scanner findings, 4 mitigated; peer 40/40 duplicates. Actual
  locations/evidence and two linked vulnerability IDs are checked, along with
  CSRF create/edit, invalid/valid login and no-access denial on the isolated copy.
* Actual RC2→RC3 image rollback: 18 complete JSON pairs equal,
  worker stopped for switching and candidate restored. Separate DB/media only.

## Unchanged skip reasons and scope limits

| Count | Existing reason |
| --- | --- |
| 151 | Skipping because V3_FEATURE_LOCATIONS is enabled. |
| 133 | Authorization is not configuration based |
| 84 | Authorization is not object based |
| 20 | This view does not inherit from <class 'rest_framework.mixins.DestroyModelMixin'> |
| 18 | This view does not inherit from <class 'dojo.api_v2.prefetch.mixins.PrefetchRetrieveMixin'> |
| 18 | This view does not inherit from <class 'dojo.api_v2.prefetch.mixins.PrefetchListMixin'> |
| 17 | Legacy authorization has no Reader/Writer/Maintainer/Owner distinction — the user is either in authorized_users (full member) or not (404). The RBAC role-gating semantics this test asserts don't apply post-Track-B. |
| 15 | Same RBAC→legacy recipient-filtering re-baseline as TestNotificationTriggers — see that class's skip note. |


All 553 reasons are in JSON. No skip/xfail is added and no original test is removed.
Experimental Dashboard-only guards are reverted with the rejected optimization;
the original behavioral R4/R5 tests remain. Legacy Selenium/chromedriver is not
claimed executed; actual browser verification uses the pinned Playwright stack.
No 20-million-row, huge Test-count tenant, external-node/HA, or prolonged production
soak is certified by this local candidate validation.
