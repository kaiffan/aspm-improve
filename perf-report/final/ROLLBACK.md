# Safe rollback

The production application patch has no migrations or indexes. Finding data does not need restoration.

On a clean checkout with the tested FINAL code, first check reverse application:

```sh
git apply -R --check perf-report/final/round4.patch
git apply -R perf-report/final/round4.patch
```

A failed check is a reason to inspect intervening changes. Do not reset or overwrite user work. Alternatively, create a normal revert of application commit `70daa20757a9b5b99836343e50791a4de8c72fd0` on the appropriate integration branch and run the tests.

Component paths for separate review/reversal:

- Products UI: `dojo/product/queries.py`, `dojo/product/ui/views.py`.
- Dashboard: `dojo/home/views.py`, `dojo/utils.py`.
- Simple Metrics: `dojo/metrics/views.py`.

Use path-restricted patches derived from CURRENT `20771ddc0b` to FINAL `70daa20757`, with `git apply -R --check`, to reverse one component. The cumulative patch is separate and should not be reversed if only Round 4 is being rolled back.

Rebuild the test image from the selected source SHA, verify its source hashes, then restart only the isolated application. The main application on port 8080 was not replaced by this work. The final test application uses port 48084.

Benchmark-only middleware, cache namespace and Celery telemetry are isolated test configuration. Restore the original runtime environment and main database URL when leaving the import copies. Stop only the `dd-final` test worker/broker when finished. Restart the three pre-existing benchmark application containers if they were initially running:

```sh
docker start django-defectdojo-uwsgi-perf-1 dd35100-round2-uwsgi-round2-1 dd35100-round3-uwsgi-round3-1
```

The snapshot databases, including the excluded no-statistics trial, and their media volumes are intentionally retained. They contain test data and credentials, so do not publish their dump files. Their removal is a separate operator decision. Do not use `down -v`, `DROP DATABASE`, index/table removal, or `VACUUM FULL` as part of this code rollback.
