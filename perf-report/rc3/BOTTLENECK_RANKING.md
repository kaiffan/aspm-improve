# RC3 bottleneck ranking — measured before performance changes

RC2 `9384826c2c2ccdbf0178ebc3faa5ea3e5513473d`, runtime source
`25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb`.
Evidence: `raw/preflight-rc2-r1-c25-mixed.json`, `raw/sql-rc2.json`,
`raw/plan-rc2.json`, `raw/profile-rc2.json`. This is a diagnostic cohort;
the final paired campaign must independently decide which fixes are retained.

| Rank | Endpoint/component | Root cause | Cost | Fix | Expected benefit | Risk |
|---|---|---|---|---|---|---|
| P1 / 1 | Dashboard and filtered Findings, scoped users | Authorization joins expose Finding to repeated per-Test bitmap heap scans; planner estimates 102 matching rows/Test versus 7,961 actual in filtered page | Scoped Dashboard chart reads 482,300 buffers, 8 heap scans, 654 ms server time; filtered page reads 162,849 buffers and sorts 63,688 wide rows for 100 results | Resolve authorized Test PKs in one SQL InitPlan, then apply `test_id = ANY(ARRAY(...))`, retaining all permission gates | Avoid repeated heap visits across the principal mixed-workload tail routes | Permission equivalence, very large Test-ID arrays; verify direct/type membership, staff, denied actions and caller queryset |
| P1 / 2 | Dashboard counters | Exact weekly counters scan the same authorized Finding relation separately from chart data | Scoped mitigated counter: 482,305 buffers, 481 ms; 3 standalone counters plus chart | Batch compatible exact aggregates; preserve unique Finding semantics and timezone boundaries | Fewer full Finding scans/request | Duplicate risk acceptances, unknown severities, date/timezone edges |
| P1 / 3 | Findings UI (standalone) | Endpoint annotations aggregate and sort the full scoped set before LIMIT | 532,569 grouped rows for 25 displayed findings, 1,029 ms server time | Select the filtered ordered page before endpoint annotations, then hydrate the same page | Remove wide aggregate/materialization before LIMIT | Stable ordering, annotation-dependent filters, pagination and race semantics |
| P1 / 4 | Findings/Test UI (standalone) | Title suggestions and CWE options evaluate large distinct scopes | Title aggregate spills 36 MiB, reads 482,306 buffers; 630 ms; CWE 401 ms | First measure authorization fix; preserve filter option semantics and suggestion set | Fewer repeat heap reads; no global cache of permission-sensitive options | Set/order of capped suggestions; no shortcut that changes available filters |
| P2 / 5 | Products full API | Exact ordered finding-ID payload aggregation | 0.45 s for admin full list, ~1.6 MiB response in prior/current profiles | Retain full payload; only optimize if paired evidence justifies it | Bounded by required output volume | API/order/count changes prohibited |
| P2 / 6 | Test UI | Product-tab count, filter options and Finding annotation work | 73–76 queries; scoped diagnostic SQL ~1.73 s | Reuse shared permission/query fix and page-first hydration if proven safe | Standalone UI gain | Jira, notes, evidence and filter preservation |
| P2 / 7 | uWSGI/runtime | Long SQL requests occupy the fixed 16 execution threads | c25: fast endpoints wait alongside expensive Dashboard/filter work | First remove measured SQL cost; retain 4×4 workers for A/B | Reduce queueing without worker inflation | Runtime changes would confound comparison |
| P3 / 8 | Detail, Tests, Engagements, Endpoints | Small direct service cost; mixed elapsed includes queue contention | Individual diagnostic API SQL mostly 1–8 ms | Verify compatibility; no speculative rewrite | Low direct gain | Unnecessary regression surface |

In the first 300-request c25 diagnostic run, Dashboard plus filtered Findings account
for approximately 61% of summed request elapsed time. This is overlapping request
time, **not CPU share**. Route tail percentiles from 15–45 requests are not used to
rank population p95; standalone samples and the paired campaign follow.

No new index or runtime change is authorized by this ranking. Sequential scans are
not inherently defects. PostgreSQL shared_preload_libraries is empty on the retained
server; pg_stat_statements is available but not loaded. Global settings and source
statistics are not changed to install it.

## Decision after incremental measurements

The Dashboard batch-count experiment at `df254707e70a0dfe467b1a7bc1389efa48d4ca54`
was **rejected** and reverted by `e00435fb1e5b2f27e2d793f5a6396c33845cd9a7`.
Compared with authorization-only, mixed p95 worsened in all three paired repeats:
2.084→2.167 s, 1.638→1.845 s, 1.687→1.982 s. RPS was essentially unchanged.
`raw/rejected-dashboard/` preserves all observations and the deliberately stopped
partial main cohort. These do not enter final A/B results. Original exact counters
and Round 5 guards remain. No original test was removed; the experimental guard
for the discarded batch query is reverted with that feature.

## Final retained decisions

| Component | Measured final result | Decision |
| --- | --- | --- |
| Scoped authorization | Mixed c25 p95 5.514→2.080 s; RPS 17.140→28.246 | Retained; 3 paired repeats, unchanged mix |
| Findings UI page/autocomplete | Standalone p95 2.302→0.633 s | Retained; n=160/build, guarded query shapes |
| Test UI page/autocomplete | Standalone p95 1.996→1.145 s | Retained; exact count and complex-filter fallback |
| Dashboard counter batching | All 3 incremental p95 pairs worsened | Rejected and reverted |
| Indexes/runtime/Celery | No demonstrated need for configuration/index change | Unchanged; no speculative tuning |
