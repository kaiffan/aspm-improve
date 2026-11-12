# Retained fixes and rejected experiments

## Release gate — independent commits

`b2d79aa1e78aee6a555e307830732ac73a2705cf` restores the real upstream
ticket-comment hook/callers and TruffleHog helper/settings. The root cause is a
partial fork integration: newer tests remained while their implementations did
not. No library, dependency or fixture substitute can supply those missing
functions. Full tracebacks, upstream SHAs and semantics are in
`RELEASE_GATE_FIXES.md`. Original default dedup fields/algorithm remain; optional
stable-ID semantics are documented for sites explicitly selecting that algorithm.
`a7da999878` separately fixes only the concurrent-index test's Timer race.

## Authorization — `8492b41e23fa4cdb71391c4712e08124f0172289`

1. Root cause: an outer Finding→Test→Engagement permission join lets PostgreSQL
   revisit heap pages for each authorized Test, with large cardinality error.
2. Before SQL/EXPLAIN: `raw/plan-rc2.json` and `raw/plan-final-rc2.json`; large
   scoped Dashboard has eight Finding heap scans and ~482k buffer accesses.
3. Change: retain anonymous/privileged-action/staff/superuser gates, resolve
   authorized unfiltered Test PKs once via ArraySubquery, then apply test_id=ANY.
   Caller queryset filters and custom registry overrides stay in place.
4. Regression: direct/type/overlapping memberships, caller filtering/order,
   denied actions, anonymous/no-membership, staff bypass and revocation. Red on
   RC2 (`scope-red-corrected.json`), green plus full suite on candidate.
5. After SQL/EXPLAIN: `raw/plan-final-rc3.json`; same authorized results with
   InitPlan and no outer per-Test Finding join.
6. Endpoint before/after: RESULTS; Dashboard/filtered API plus scoped diagnostic
   actors. Complete JSON/context comparisons verify correctness.
7. Mixed before/after: all 30 paired main runs in RESULTS; unchanged workload.
8. Permissions: full authorization/Product/Finding suites, actual no-access
   browser/API cases and full payload hashes; no permission-sensitive global cache.
9. Writes: no schema, index, counter, model-save or import-path change. No new
   write/index maintenance. Test-ID array memory scales with authorized Test count,
   not Finding count; very large Test-count tenants remain an explicit limit.
10. Rollback: ordinary independent revert or exact RC2 images; no schema action.

## UI page and autocomplete — `f21b611ef4888533dfd2252a0c59ed254ae68e67`

1. Root cause: endpoint COUNT annotations GROUP BY the entire Finding scope
   before LIMIT; title DISTINCT may walk a global title index for a small scope.
2. Before plans: initial/final RC2 plans and `raw/autocomplete-alternatives.log`.
   532,569 grouped rows for 25 results; ~574k unrelated title-index rows discarded.
3. Change: one SQL snapshot selects the authorized, filtered, ordered PK page
   before annotation. Test UI paginates before prefetch. A bounded authorized
   projection precedes DISTINCT for Test-array autocomplete scopes; compiler SQL,
   quoted model field and bound values prevent SQL injection or scope widening.
4. Regression: page/order/count, caller non-mutation, evaluated/unsliced behavior,
   exact capped authorized words, revocation and Test UI permissions. The extra
   related-sort guard reproduced two copies of a Finding on a page of size one.
   `49066c037bc38a3795cad00ded7dd95f2fd16c96` retains the original path for related,
   random or custom ordering rather than changing its grouping/cardinality.
   `6c2e69590c68879e12610f8dcb7c8eb3f700a348` applies the same conservative
   fallback to multiplying to-many filters and unsupported query shapes, with
   a separate red/green page-boundary test. The existing join detector is moved
   unchanged to query_utils and remains importable from filters.
   `ccfd52d372695176485e65000b4270e01d7dfb1b` uses the same eligibility guard
   before Test UI counting, preserving count=2 rather than 3 for overlapping
   expired acceptances. Its regression was observed red before the fix and green
   afterwards; both summaries remain in raw/.
5. After plans: final RC3 page GROUP BY is bounded by the PK subquery. Related
   ordering is deliberately not optimized. Capped suggestion semantics stay
   unordered/plan-dependent as before; actual filter predicates are unchanged.
6. Endpoint before/after: both RC2 and authorization-only UI controls, n=160,
   plus final candidate in RESULTS / before-after-ui-fixes chart.
7. Mixed: incremental authorization-only vs retained RC3 runs and the complete
   final main A/B. UI-only routes remain outside the mix.
8. Permissions: original predicates remain inside the subquery and hydration;
   complete actor/context/JSON checks plus real pagination/browser matrix.
9. Writes: none in the optimization; no new index, schema or cache invalidation.
   Real importer/dedup/evidence checks run only on the separate validation copy.
10. Rollback: independent UI revert or RC2 images; all data remains compatible.

## Dashboard batching — rejected

`df254707e70a0dfe467b1a7bc1389efa48d4ca54` combined two exact counters, but all
three incremental pairs worsened mixed p95 while RPS stayed effectively flat.
It was reverted by `e00435fb1e5b2f27e2d793f5a6396c33845cd9a7`. Fewer SQL statements
did not reduce total cost: the merged DISTINCT aggregate lost the advantage of
separate selective paths and increased aggregation work. Every observation is
retained in `raw/rejected-dashboard/`, and no rejected result enters the final table.
Original exact counters remain, accelerated by the retained authorization shape.
