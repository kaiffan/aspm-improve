# Reproducing Round 3

Use the isolated Round 2/3 A/B proxy on `http://127.0.0.1:48083`, with `X-DD-Perf-Variant: before` selecting Round 2 and `after` selecting Round 3. Port 8080 is the original build. The candidate image is `dd-api-round3:3.5.100`; its hashes are in `after_image_hashes.txt`. It inherits `dd-api-round2:3.5.100` and copies only the patched `dojo/finding/api/filters.py` into `/app/dojo/finding/api/filters.py`.

Keep credentials outside Git in a mode-0600 JSON file containing a list of 25 objects with `token`, `product` and `finding` properties. The Product and Finding IDs must be visible to that account. Use 1 admin and 24 distinct restricted identities for this experiment. Pass this file through stdin; do not put token values in command arguments or terminal output.

Example single series (run from this directory):

```sh
python3 mixed_load.py --url http://127.0.0.1:48083 --variant before \
  --concurrency 5 --requests 300 --warmup 25 --seconds 150 --timeout 20 \
  --seed 35101 --stop-file /tmp/dd-r3-stop --output c5-r1-before.json \
  < /private/path/accounts.json
```

Repeat with concurrency 1, 5, 10, 15, 25, inspecting resource measurements before increasing it. At each level run BEFORE, AFTER with seed 35101, then AFTER, BEFORE with seed 35102. Final reported files have prefix `ab_c`; each variant has 600 measured requests per level. Use AC power with Low Power Mode disabled; keep macOS awake for the bounded experiment. Do not reuse files from the interrupted or power-transition subdirectories in the final comparison.

Resource collector (macOS + Docker; first two arguments are output and stop-file, followed by duration and web container names):

```sh
python3 monitor.py metrics.jsonl /tmp/dd-r3-stop 900 \
  dd35100-round2-uwsgi-round2-1 dd35100-round3-uwsgi-round3-1
```

Run the collector alongside the benchmark and use the same stop-file. It samples the existing local PostgreSQL/Valkey containers and writes no query values. Per-worker RSS was sampled inside each web container with `DD_RSS_DURATION=900` and `python - < worker_rss.py`. Both collectors stop after their duration; the load runner also has an HTTP error circuit breaker and a per-series deadline. A pre-existing stop-file intentionally prevents a run: review its cause before using a new path.

Regression modules executed through `run-unittest.sh --test-case` in a separate test database: `unittests.test_api_finding_relation_filters`, `unittests.test_api_finding_filter_no_multiply`, `unittests.test_local_release_performance_checks`, `unittests.test_api_product_prefetch`, `unittests.test_apiv2_prefetch_test_finding_groups`, `unittests.test_authorization_queries`. See `verification.txt` for outcomes. Do not point the unit-test runner at the million-finding database.

The import fixture experiment used the supported import/reimport API, two isolated products and 40 ZAP alerts with three URLs each. Results are in `import_idle.json`, `import_loaded.json` and `import_celery.json`. It temporarily enabled deduplication and restored its original False setting. Do not repeat the import merely to reproduce read-only measurements: its 168 fixture findings are retained separately from the original million.
