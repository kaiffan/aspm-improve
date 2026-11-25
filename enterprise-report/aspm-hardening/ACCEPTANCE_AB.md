# Acceptance A/B

Full 1M, 10-VU Acceptance with three independent restores is NOT TESTED for this candidate. Required p90 thresholds remain import 400 findings E2E <=110s, Finding Browser open <=60s, Finding POST <=5s, native HTML report E2E <=70s. HTTP 2xx alone is insufficient: the frozen runner checks business findings/tests/evidence and restoration integrity.

The portable native wrapper selects A=25da29aa and the final B application SHA while preserving frozen acceptance workload/checksums and SLOs. Results from ARM64/local synthetic fixtures must not be promoted to Ryzen/Linux AMD64 results. No SLO pass or performance review pass is assigned without complete provenance-matched cohorts.
