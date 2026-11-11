# Reproduce the final comparison

Use an isolated local stand with the existing 1,000,168 findings and compatible 3.5.100 schema. The measured main workload uses standard full API payloads. `findings=count`, `findings=none` and `fast_offset=1` are separate scenarios. The original port 8080 is not the optimized variant.

## Sources and runtime

- ORIGINAL: official `3.5.100`, `334bef02d65a74909fe976b22724526474d5a0f6`.
- CURRENT: `20771ddc0bdfb4b763708f70e1cd6c131c3f6b5e`.
- FINAL application source: `70daa20757a9b5b99836343e50791a4de8c72fd0`.

Image IDs and the pinned common runtime are in `environment.json`. Every image replaces the entire `/app/dojo` tree with its selected Git source, eliminating old image patches. Dependencies, entrypoints and assets outside that tree use the same common runtime. Do not substitute a floating `latest` image. The seven release-normalization files and restored runtime-only Finding patches are listed in `integration_manifest.json`; functional HA/SCM/custom Engagement UI work from the main checkout was not included.

From the performance branch, in a new empty private directory:

```sh
DD_R4_DIR=/private/tmp/aspm-final-reproduce
python3 perf-report/final/build_images.py --repo . \
  --base-image dd-api-perf-base:3.5.100 --contexts-dir "$DD_R4_DIR/build"
python3 perf-report/final/prepare_stand.py --private-dir "$DD_R4_DIR" \
  --runtime-env /private/path/runtime.env
docker compose -p dd-final -f "$DD_R4_DIR/compose.json" up -d web nginx
```

The runtime env file must remain outside Git, mode 0600. Use the existing 3.5.100 database/broker/cache/secret configuration. In the original measurement it was `/private/tmp/dd-35100-round4/runtime.env`. Compose never starts an initializer, runs migrations or deletes a volume. Bind is localhost:48084 only. It expects the existing `django-defectdojo_default` network, `postgres`/`valkey` aliases and media volume. Adjust only these environment-specific names when reproducing elsewhere, and record the difference.

`verify_sources.py "$DD_R4_DIR"` verifies image code against preserved build contexts and Git blobs. The source hash JSON files from the completed run are included. `official_tag_verification.txt` records the independent upstream ref check.

## Credentials and permission model

`actors.json` contains public scenario IDs and existing test-user names. The dataset has one existing superuser and 24 `r3_perf_reader_00..23` accounts with Product membership in three cohorts. Passwords are unusable; tokens and session cookies are never committed. Resolve them directly to a private file:

```sh
python3 perf-report/final/prepare_credentials.py --output "$DD_R4_DIR/accounts.json"
```

This creates sessions for those existing accounts, not new permissions. The resolver refuses to overwrite a file. If these accounts do not exist, prepare equivalent isolated test users explicitly; do not use someone else's real credentials. Required JSON fields are `token`, `session`, `product`, `finding`, `test`, `engagement`. The runner receives this JSON via stdin, never through token command arguments.

## Dataset snapshot and planner statistics

Create a consistent snapshot and **ANALYZE the canonical copy before cloning**. The script refuses existing database names and never drops/replaces one:

```sh
bash perf-report/final/snapshot_databases.sh dd_round4_repro_
```

The finished run used `dd_round4_seed`, then final write copies `dd_round4a_original/current/final` cloned after ANALYZE. The first write trial had zero finding column-statistics and was archived in `background_unanalyzed/`; it is excluded from final results. Final copies must have statistics in `pg_stats` before measurement. All writes use copies, a separate broker and separate media. The primary remains unchanged.

The original read-only experiment switched one active application container against the unchanged primary database. A constant-memory full-row fingerprint before/after matched the immutable seed. If other users can write to the stand, point all read variants to a separate controlled copy instead and record its identity.

## Read matrix

Keep AC power, Low Power Mode disabled and macOS awake. Record the initial state of old benchmark web containers, stop only those for equivalent resource availability, and restore them afterwards. Do not tune uWSGI or PostgreSQL between variants.

```sh
caffeinate -i python3 perf-report/final/run_suite.py \
  --compose "$DD_R4_DIR/compose.json" --credentials "$DD_R4_DIR/accounts.json" \
  --phase profile --stop-file "$DD_R4_DIR/stop-profile"
python3 perf-report/final/check_compatibility.py
caffeinate -i python3 perf-report/final/run_suite.py \
  --compose "$DD_R4_DIR/compose.json" --credentials "$DD_R4_DIR/accounts.json" \
  --phase endpoints --stop-file "$DD_R4_DIR/stop-endpoints"
caffeinate -i python3 perf-report/final/run_suite.py \
  --compose "$DD_R4_DIR/compose.json" --credentials "$DD_R4_DIR/accounts.json" \
  --phase mixed --levels 1 --requests 100 --label-prefix mixed-c1 \
  --stop-file "$DD_R4_DIR/stop-mixed-c1"
caffeinate -i python3 perf-report/final/run_suite.py \
  --compose "$DD_R4_DIR/compose.json" --credentials "$DD_R4_DIR/accounts.json" \
  --phase mixed --levels 5,10,15,25 --stop-file "$DD_R4_DIR/stop-mixed"
caffeinate -i python3 perf-report/final/run_suite.py \
  --compose "$DD_R4_DIR/compose.json" --credentials "$DD_R4_DIR/accounts.json" \
  --phase users --stop-file "$DD_R4_DIR/stop-users"
```

The suite writes to its adjacent `raw/` directory. Preserve existing observations or use a fresh report directory before a rerun. Endpoint series: 2×40 measured, 5 warmup. Mixed c=1: 2×100; other levels: 2×300, 25 warmup each. Round order ABC then CBA, seeds 35101/35102, same port and schedules. Saturation uses a rotating pool of 25 identities. User mode fixes each worker's identity and request sequence and adds 0.25 s think time. HTTP timeout is 90 s, series deadline 300 s; incomplete series are not successful results.

`monitor.py` records sampled Docker CPU/memory, PG connections/activity/buffers/temp/locks, Celery queue, host swap/pressure and power. `worker_rss.py` samples per-worker Linux RSS every 0.4 s. Resource/HTTP stop files stop escalation; inspect the cause before selecting a new path. Never silently reuse a failed trial as a completed point.

All three applications mount the identical `perf_instrument.py` middleware. It emits only SQL count/time headers. Query text/params, credentials and response bodies are not logged by it. Cache backend stays unchanged; only a unique namespace isolates variants/runs. Simple Metrics warm-cache and fresh-render endpoints are separate. Fresh render uses a deterministic, ignored query parameter to force a cache miss; it is not in the primary mixed workload.

## Imports and background tasks

Only after read phases finish:

```sh
caffeinate -i python3 perf-report/final/run_background.py \
  --compose "$DD_R4_DIR/compose.json" --runtime-env /private/path/runtime.env \
  --credentials "$DD_R4_DIR/accounts.json" --private-dir "$DD_R4_DIR" \
  --db-prefix dd_round4_repro_ --media-prefix dd-final-repro-media- \
  --redis-offset 6 --stop-file "$DD_R4_DIR/stop-background"
python3 perf-report/final/verify_background.py
python3 perf-report/final/fingerprint.py --reference dd_round4_repro_seed \
  --output perf-report/final/fingerprint_reproduce.json
```

The harness checks database name, initial count and outbound integrations before imports. It uses Product 2 (633,794 findings before the test), product-wide deduplication, six isolated Engagement sequences per variant, 40 ZAP alerts and three URLs/evidence pairs per alert. Read control and loaded phases use 600 requests at c=10, with explicit warmup. Celery uses one process, prefetch 1, soft/hard limits 90/120 s; broker DBs 6/8/10 and media are isolated. There is no beat in the copied stand. No bulk-create seeding substitutes for real import API calls. All added scan findings remain in the copies.

## Tests and artifacts

Use `run-unittest.sh --test-case` with a separate test PostgreSQL, matching the tested image and the repository `unittests/` and `tests/` mounted. Required modules and results are in `TEST_RESULTS.md`. The measured test setup used local test dependencies `vcr`, `vcr_unittest`, `wrapt`, `parameterized` from the existing devdeps image; these are not added to benchmark application images. Never point unit tests at the million-finding database.

A secret-free example is `compose.tests.json`; set `DD_R4_SOURCE` to the absolute checkout and provide `DD_R4_TEST_ENV` / `DD_R4_TEST_DB_PASSWORD` privately. Build the same thin test image with `Dockerfile.tests` and the existing local devdeps image, then run:

```sh
docker build -f perf-report/final/Dockerfile.tests -t dd-final-final-check:3.5.100 .
COMPOSE_FILE=perf-report/final/compose.tests.json COMPOSE_PROJECT_NAME=dd-final-tests docker compose up -d
COMPOSE_FILE=perf-report/final/compose.tests.json COMPOSE_PROJECT_NAME=dd-final-tests \
  ./run-unittest.sh --test-case 'unittests.test_round4_performance unittests.test_dashboard unittests.test_api_finding_relation_filters unittests.test_api_finding_filter_no_multiply unittests.test_local_release_performance_checks unittests.test_api_product_prefetch unittests.test_apiv2_prefetch_test_finding_groups unittests.test_authorization_queries'
```


```sh
python3 perf-report/final/analyze.py
python3 -m venv "$DD_R4_DIR/chart-venv"
"$DD_R4_DIR/chart-venv/bin/pip" install -r perf-report/final/chart-requirements.txt
MPLCONFIGDIR="$DD_R4_DIR/mpl-cache" \
  "$DD_R4_DIR/chart-venv/bin/python" perf-report/final/plot_results.py
python3 perf-report/final/build_reports.py
```

Percentiles are computed from pooled request samples, never averaged across endpoints or runs. RPS uses total measured requests divided by summed measured duration. p99 requires at least 300 successful samples. Sampled CPU peaks and PG counter deltas have the polling limitations described in the report. Preserve raw JSON/JSONL, source identities and all excluded trials. See `ROLLBACK.md` before restoring the stand; do not delete databases or volumes as cleanup.
