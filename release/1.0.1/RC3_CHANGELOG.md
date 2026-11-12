# ASPM 1.0.1 RC3 changes

Release-gate and performance changes are separate commits. The detailed
before/after SQL, tests, endpoint/mixed measurements, permission checks and
rollback are in `perf-report/rc3/FIXES.md`.

* Fixed: missing ticket-comment production implementation and callers.
* Fixed: missing TruffleHog v3 identity helper and default-off folding option.
* Fixed: timing race in the concurrent-index test fixture.
* Performance: authorize Findings through one Test-ID SQL scope.
* Performance: batch exact Dashboard weekly counts.
* Performance: hydrate Finding UI pages after selecting their PKs.
* Performance: avoid global title-index walks for scoped autocomplete.
* Release metadata: 1.0.1 remains unchanged; candidate channel advances to rc3.
