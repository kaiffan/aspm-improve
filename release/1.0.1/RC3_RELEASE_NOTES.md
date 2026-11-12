# ASPM 1.0.1 RC3

Candidate based on RC2 `9384826c2c2ccdbf0178ebc3faa5ea3e5513473d`.
Exact runtime source and local Docker image identities are recorded in
`perf-report/rc3/raw/build-final.json`. No Stable tag is published.

* Restore the actual upstream ticket-comment hook and TruffleHog stable-ID
  helper whose tests were already present in RC2. No tests are hidden or skipped.
* Resolve scoped Finding access through authorized Test PKs inside each SQL
  statement, avoiding repeated Finding heap scans. Permission gates and custom
  authorization registry overrides remain in place.
* Select ordered Finding page PKs before endpoint annotations, including Test UI.
  Filtering, counts, sorting, evidence and pagination contracts are preserved.
* Keep capped autocomplete DISTINCT over its authorized projection to avoid
  walking the global title index for a small scope. No shared permission cache.
* Synchronize the existing concurrent-index migration test with observed polling
  instead of a timer; migration code and schemas are unchanged.

The Product full REST payload remains the default. No runtime worker increase,
new index, migration, dependency update, palette/branding/navigation/theme change
is included. Performance claims and remaining limitations belong to the new
paired campaign in `perf-report/rc3/RESULTS.md`, not historical Round 5 numbers.
Batching the weekly Dashboard counters was tested and rejected: all three
incremental mixed pairs worsened p95 without a throughput benefit. Original exact
counter queries are retained; the authorization change reduces their heap cost.

TruffleHog: the default Hash Code algorithm and existing hash fields do not
change. v3 findings now have the upstream stable unique ID. Sites explicitly
using the Unique ID from tool algorithm must review their historical findings
before changing dedup configuration. `DD_TRUFFLEHOG_FOLD_COMMITS` defaults to
false; do not enable it, mass-recompute identities, or run dedup migrations as
part of this upgrade.

Rollback: deploy the exact recorded RC2 app and gateway images, stop the RC3
worker first, and retain all databases/volumes. There is no schema downgrade.
See `perf-report/rc3/ROLLBACK.md` for validation and data-integrity checks.
