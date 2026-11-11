# Reproduce Round 5

These are real local read-only measurements on the existing database, not a production capacity claim. The source/image mapping is in `source_verification.json`; all three images use the same pinned `dd-api-perf-base:3.5.100` runtime. ORIGINAL is the official release tag, Round 4 is the completed fork, Round 5 is application commit `c6a6144ed93b83adb1fd4ea9daa2c5e417ecea37`. The later report commit does not change application code.

## Safe local stand

Use the previous round's `perf-report/final/prepare_stand.py` with a private directory and the existing private runtime env file. Adapt only the isolated project name to `dd-r5`, localhost port to 48085 and middleware bind to this directory's `perf_instrument.py`. The completed run's private config is `/private/tmp/dd-35100-round5/compose.json`; credentials are `/private/tmp/dd-35100-round4/accounts.json`. These files contain secrets and are deliberately absent from Git. Do not use port 8080 as the optimized application. No initializer, migrations or additional Celery worker is started against the shared database. Stop other old benchmark application containers during the comparison and restore their initial state afterwards.

Build Original and Round 4 using `final/build_images.py` or reuse the immutable image IDs verified in this report. Build Round 5 by exporting the entire `dojo` tree at the application SHA into an empty context, preserving symlinks, and copying it over the same pinned base image after removing only the image's `/app/dojo` tree. This image build operation does not touch PostgreSQL or Docker volumes. Name the resulting image `dd-r5-final:3.5.100`; `python3 perf-report/round5/build_image.py --context /private/tmp/empty-r5-build` performs this export/build. `verify_sources.py` compares every ordinary application source file to its Git blob.

Keep the same database/schema, dependencies, four uWSGI processes/four threads, PG settings and resource limits for all variants. Leave server settings unchanged. Use AC power, low power mode off and the bounded resource monitor. The measured machine had no new data generation/imports during this round.

## Load protocol

`benchmark.py`, `scenarios.json` and `run_suite.py` preserve the Round 4 mixture: Findings 30%, Product/severity/active filtered findings 15%, Finding detail 10%, **full** Products API 10%, Tests 10%, Engagements 5%, Dashboard 10%, Products UI 5%, Endpoints 5%. Product modes `count`/`none` and FAST OFFSET are excluded from this mixed workload. URLs and page size 100 are unchanged.

Use one existing admin plus 24 existing scoped reader accounts, resolved privately using the previous credential helper. `actors.json` contains only non-secret scenario metadata. No tokens, passwords or cookies belong in arguments, reports or shell output. The runner reads credentials on stdin through the controller.

```sh
caffeinate -i python3 perf-report/round5/run_suite.py \
  --compose /private/path/compose.json --credentials /private/path/accounts.json \
  --phase mixed --variants original,round4,round5 --levels 1,5,10,15,25 \
  --repeats 2 --stop-file /private/path/new-stop-file
```

Each series has 25 warmup requests, 100 measured requests at c=1 and 300 at each other concurrency. Seeds are 35101/35102; build order ABC then CBA. The fixed tuple schedule rotates the same 25 identities, with zero think time. **Concurrency is the number of in-flight requests, not 25 independent human sessions.** The report does not describe this as a user-capacity certification. Timeout 90 s, per-series deadline 300 s. The monitor stops on power changes, OOM/stopped containers, repeated monitoring failures, high memory pressure/swap growth. Inspect any stop-file before starting a new series; do not delete it to hide a failed run.

Endpoint series use the same 25-identity pool, 5 warmup requests, two repeats of 40 measured requests per case. Run `--phase endpoints --cases products,dashboard,web_products,web_findings,web_test --endpoint-concurrency 1 --requests 40 --repeats 2`; then Products alone at c=5/10/25. These standalone scenarios have a different mixture from the primary workload and are presented separately.

## SQL and correctness

`pg_stat_statements` is not enabled. Benchmark middleware always emits only SQL count/time headers. For bounded SQL-shape diagnostics set `DD_R5_SQL_LOG=1` identically, recreate the candidate and run the same c=25 test, then copy `/tmp/r5-sql.jsonl` privately into the diagnostic artifacts. The log captures the original SQL argument with string literals redacted, never bound values or `cursor.query`. Driver wall time is not exact server-only execution time. Warmup/readiness are included in diagnostic SQL call counts and excluded from primary HTTP samples.

`profile_phases.py` runs through Django's real HTTP client and times SQL, Product ID loading, serializer representation, JSON rendering and inclusive template rendering. RSS is sampled every 10 ms and is a lower bound on an interval peak; sequential requests may reuse Python memory. Run `capture_profiles.py` only between load phases. Its recorded `EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, FORMAT JSON)` plans are safe SELECTs in a quiet stand, not concurrent latency samples. Actual row counts and buffers are available for those plans; aggregate per-query PG buffer counters and server-side SQL p95 are unavailable without pg_stat_statements/appropriate tracing.

Use the previous round's `profile.py` through `--phase profile` for complete JSON hashes and selected server template context, including both admin/scoped users and opt-in modes. Run tests with `run-unittest.sh` against the separate test PostgreSQL, never the million-finding database. New regression tests fail on Round 4 and pass on the final application. No parser/import/deduplication implementation was changed; the previous real import/reimport results remain historical, not new Round 5 experiments.

```sh
python3 perf-report/round5/analyze.py
MPLCONFIGDIR=/private/tmp/mpl-r5 XDG_CACHE_HOME=/private/tmp/cache-r5 \
  /path/to/matplotlib-venv/bin/python perf-report/round5/plot_results.py
```

Aggregation pools actual request latencies, does not average percentiles. p99 requires ≥300 successful observations, p95 ≥20. Black ticks/individual replicate values expose spread; no smoothing. Per-case mixed RPS is its share of total elapsed mixed throughput, not standalone capacity. Latency contribution is a sum of overlapping elapsed request times including queues, not exclusive CPU time. Raw requests and resource samples are retained under `raw/`. Rejected exploratory chart-plan results are archived separately and excluded from the final tables.
