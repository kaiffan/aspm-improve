# Reproduce RC3 on the retained local lab

Use branch `perf/1.0.1-rc3-optimization` in its separate worktree. RC2 remote HEAD
was verified with `git ls-remote`: `9384826c2c2ccdbf0178ebc3faa5ea3e5513473d`.
Runtime RC2 source is `25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb`. The accepted
RC3 runtime source and exact images are in `raw/build-final.json`. Subsequent
report-only commits must have no diff under `dojo/` against that source.

## Safety and prerequisites

The explicit private input `RC2_PRIVATE` contains the retained RC2 Compose
configuration and 25 existing accounts. It is outside Git, directory mode 0700,
files 0600. `RC3_PRIVATE` defaults to the sibling `aspm-rc3-private` directory.
For another host, provide its reviewed private configuration explicitly; do not
guess credentials or point the lab at a database based only on a familiar name.
The benchmark is loopback-only at port 48092, on `dd_round4_seed`, with no worker
or beat and read-only media. The source database is read only for fingerprints.
Never run migrations, write tests, a test runner, or a worker against source/seed.
No volume deletion, database deletion, destructive migration or schema downgrade
is part of this runbook. Existing evidence is never overwritten.

Stop unrelated app/worker/benchmark stacks during performance measurements.
The retained RC2 demo was stopped for both A and B to remove background work.
Keep AC power, low-power mode off, Docker VM 10 CPU / 7.82 GiB, no per-container
limits, uWSGI 4 processes × 4 threads, the same dependencies and PostgreSQL
statistics. Do not run full suites, builds, browser audits, tracing profiles or
package installs during load. Resource guard stops on OOM, memory pressure,
swap growth, power changes and repeated HTTP errors; investigate every stop.

## Commands

```sh
git branch --show-current
git rev-parse HEAD
git ls-remote origin refs/heads/release/1.0.1-rc2
python3 perf-report/rc3/scripts/lab.py setup
python3 perf-report/rc3/scripts/run_tests.py --label independent-full
node --test release/1.0.1/scripts/theme.test.cjs
```

`run_tests.py` uses `./run-unittest.sh`, mounts the chosen source read only, and
asserts an internal-only test network and the dedicated retained test volume.
No test discovery exclusion or skip override is applied. The runner preserves
the test database. Full-suite source SHA, actual methods, errors, failures and
all skip reasons are recorded. Copy its successful summary to the campaign's
expected marker only after checking it matches the chosen runtime tree.

Build from exact committed source and the checked-in dependency digest lock:

```sh
python3 release/1.0.1/scripts/build_images.py \
  --sha <accepted-runtime-sha> --context <new-empty-context> \
  --manifest perf-report/rc3/raw/build-final.json
caffeinate -dimsu python3 perf-report/rc3/scripts/campaign.py
python3 perf-report/rc3/scripts/sql_audit.py
python3 perf-report/rc3/scripts/validate_copy.py
python3 perf-report/rc3/scripts/html_variation.py
RC3_BUILD_CONTEXT=<the-build-context-above> \
  python3 perf-report/rc3/scripts/final_checks.py
python3 perf-report/rc3/scripts/analyze.py
<qa-venv>/bin/python perf-report/rc3/scripts/plot.py
python3 perf-report/rc3/scripts/report.py
```

Use a fresh evidence output directory/cohort or archive the whole previous one
with its reason. Do not remove selected slow/error samples. `campaign.py`
refuses an existing main cohort and an unsuccessful full-suite marker. Its
intermediate build manifests identify authorization-only and the retained RC3.
The rejected Dashboard manifest is preserved solely for diagnostic replay.
No Docker image is pulled implicitly or pushed to a registry by this workflow.

The SQL audit streams a read-only seed dump into its own new PostgreSQL volume,
enables pg_stat_statements only there and ANALYZEs once before either variant.
It refuses to overwrite an existing audit database. Server windows include
warmup and stay separate from the primary cohort. The validation step creates a
separate database/media copy, runs actual writes/browser/rollback checks, drains
active/reserved/scheduled/queued Celery tasks, then removes diagnostic hooks.
The final checks verify every application/static file against the build context,
identical installed dependencies, image labels/digests, and local RC3 aliases.
Matplotlib belongs to a separate QA virtual environment, never application
dependencies. Playwright/Chromium/axe versions are retained from the RC2 QA setup.

## Workload and statistics

The unchanged `perf-report/round5/benchmark.py` generator uses Findings 30%,
Product/severity/active filtered Findings 15%, detail 10%, **full Products 10%**,
Tests 10%, Engagements 5%, Dashboard 10%, Products UI 5%, Endpoints 5%.
Limit 100, 25 existing identities, no think time; concurrency is simultaneous
requests, not a user-count model. Seeds 35101/35102/35103 determine the same
request/actor schedules on A and B. Each run has 300 measured + 25 warmup
requests. Levels are 1/5/10/15/25; three independent paired repeats, order
A/B, B/A, A/B. No `findings=count/none` or FAST substitution enters the mix.

Standalone endpoints have 160 measured + 5 warmup requests, c1. Findings UI and
Test UI are additional standalone routes only. Authorization-only UI runs
separate the shared authorization change from the page/autocomplete fixes.
No route p95 is reported with fewer than 100 observations; p99 requires 300.
Mixed percentiles are pooled from raw observations, not averaged repeat
percentiles; RPS is total requests / total measured elapsed. Warmup is excluded.

Resource samples are filtered to each measured HTTP window. SQL execute wall
includes waiting/network effects and is not PostgreSQL CPU. Summed overlapping
request elapsed is not processor utilization. Worker RSS may double-count
shared pages; container memory and per-worker RSS are reported separately.
Allocation/CPU tracing and cProfile run in separate diagnostic processes and
are never used as HTTP latency observations. No missing metric becomes zero.

Integrity checks include count, sum of IDs, XOR over complete row text and a
streamed SHA-256 over ordered `(id, SHA-256(full row text))` pairs, with fixed
UTC/DateStyle. Both original source and protected seed must remain identical
before/after load and after write validation on a separate copy.
