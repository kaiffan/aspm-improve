# ASPM 1.0.1 RC3 known issues and measurement limits

* The full suite retains 553 existing skips, including legacy/RBAC and V3-gated
  variants. Their reasons are listed, not hidden. No new skip or loader error.
* Default Product full payload still contains all ordered active Finding IDs;
  exact counts and broad aggregates retain unavoidable cost on large scopes.
* Authorization Test-PK arrays are measured on the million-Finding / roughly
  hundred-Test seed. Tenants with very large Test counts need separate scale
  validation; no claim is made for every cardinality distribution.
* Related/random/custom Finding orderings, multiplying to-many filters and
  unsupported query shapes retain the original annotation/LIMIT path for
  correctness, and therefore do not receive the page-first speedup.
* Autocomplete's existing unordered DISTINCT/LIMIT cap remains plan-dependent.
  Tracemalloc snapshots can show bounded allocation increases; container/worker
  memory is reported separately and no universal memory reduction is claimed.
* Restored TruffleHog stable IDs are additive. Sites explicitly using Unique ID
  from tool should review historical imports before changing dedup configuration.
  Folding remains off; no automatic mass recomputation or data migration.
* Benchmarks are local fixed-count saturation tests. External HA/PostgreSQL,
  long production soak, 20-million-row datasets and legacy Selenium are not
  certified. Runtime worker count, broker, indexes and statistics are not tuned.
* The candidate is a local build, not an automatically published Stable release.
