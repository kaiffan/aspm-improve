# Performance qualification

| Variant | Source |
| --- | --- |
| A | `0011c221aba7d968ae0734dc1897a087fd9d55e6`, Enterprise Hardening tip |
| B | `7328daa441129bad49abd956e273e624362e655e`, integrated application and deployment checkpoint |

This Apple Silicon lab provided local route diagnostics and did not run the strict native performance campaign. Host architecture and available disk are recorded separately. The Core9 and Acceptance A/B gates are NOT TESTED. No prior baseline percentile is credited to B. [Native build plan](raw/native-build-plan.json) · [Capacity](raw/capacity.json)

Use the existing frozen nine-route mix, unchanged seeds and weights and native Linux AMD64 worker. Restore the same sealed one-million-Finding snapshot for each variant. Keep worker count, cache isolation, PostgreSQL settings, memory limits and credentials constant. Run concurrency 1, 5, 10, 15 and 25 with at least three repetitions at the principal points. Collect latency percentiles, requests/sec, errors, query counts, PostgreSQL and application CPU, I/O, memory, WAL and locks.

Run Acceptance at 10 VU with three independent restores. Required p90 thresholds are 110 seconds for Import 400, 60 seconds for Finding Browser Open, 5 seconds for Finding POST and 70 seconds for native HTML export. Confirm business effects after each operation.

Benchmark identity logins, grant cardinality, authenticated workspace routes, same-Repository enrollment, webhook delivery and group revocation separately from Core9. The local query run saw 14 SQL statements per Commit Overview request for each role at 1, 100 and 1,000 accepted ScanRuns. Projects and Reports each used eight. Findings used 58–59 and the policy page 12–13. A User with 256 asserted entitlements kept the TEST-only scope in a database containing 10,000 temporary mappings. That listing used eight SQL statements in all three repeats. These are route diagnostics on synthetic fixtures, with three repeats per case. [Local query evidence](raw/query-counts.json) · [Reproduce](REPRODUCE.md)

Verified all 106 frozen workload files against the versioned lock. The protected million-Finding database and its filesystem snapshot were not read or modified for this run. [Frozen workload hashes](raw/native-workload-checksums.json)
