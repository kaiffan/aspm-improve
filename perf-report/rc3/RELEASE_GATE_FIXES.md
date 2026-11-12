# Release-gate fixes, independent of performance changes

The two loader errors were reproduced on the unchanged RC2 runtime image with
full `unittests` discovery: `raw/discovery-red.log`. Neither is a dependency,
packaging, import spelling, fixture, or library-version problem.

Commit `20771ddc0bdfb4b763708f70e1cd6c131c3f6b5e` integrated the cumulative
performance work onto the 3.5.100 runtime. The Git tree retained newer upstream
tests while the corresponding production implementations were absent.

* `unittests.test_ticket_comments`: upstream
  `f38e79a0ed9613de23a14f0fbeeab143b2d35140` added the actual ticket-comment
  registry, SLA dispatch and risk-acceptance dispatch together with these tests.
  Restore precisely that module and its two caller changes. With no registered
  handler/link filter, existing behavior is preserved. Exceptions from handlers
  remain isolated; no outbound integration is registered or contacted by this fix.
* `unittests.tools.test_trufflehog_parser`: upstream
  `6466dda8a41ee47834f42d0b08b6b1ee8297b276` added the stable identity helper,
  parser integration and default-off `DD_TRUFFLEHOG_FOLD_COMMITS` setting together
  with the already-present test vectors. Restore those changes. This is real
  parser functionality, not an import stub. Existing default Hash Code dedup
  fields/algorithm and per-commit in-report grouping are unchanged. Instances
  explicitly using Unique ID from tool must review the additive v3 ID semantics;
  do not enable folding or run a mass identity recomputation as part of upgrade.

No tests are deleted, excluded, skipped, renamed, weakened or replaced. Green
full discovery loads **8,693** tests (the formerly failed modules now contribute
their actual methods): `raw/discovery-green.log`. Ruff 0.16.10 passes for all five
changed production files. Full-suite execution is recorded separately in
`raw/full-blocker-tests.json`; discovery alone is not a passing full suite.

Rollback is an ordinary revert of the standalone release-gate commit. It restores
both loader failures and must block promotion again. There is no schema migration
or dependency change.
