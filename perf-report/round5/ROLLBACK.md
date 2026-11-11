# Safe rollback

No migrations, index changes, server setting changes or dataset writes were introduced. Database rollback/restoration is unnecessary.

* Roll back the three Round 5 application commits (`26e232e2de62561fe4670f4fa7f407500c20854b` `ef29615d0c55aa3c78114bf2797f8a0c2e6cc10d` and `c6a6144ed93b83adb1fd4ea9daa2c5e417ecea37`) in reverse order on a separate integration branch, or deploy the verified Round 4 image `dd-final-final:3.5.100` (source `716efb463387f82a0d13d5eae2541ac6b7dfee96`, same application as `70daa20757a9b5b99836343e50791a4de8c72fd0`). Keep every existing DB volume.
* Product-only rollback: restore `dojo/product/queries.py`, `dojo/product/api/views.py`, `dojo/query_utils.py`, and `dojo/finding/api/filters.py` from Round 4 together. The latter two files only move the existing Test-ID array lookup into a reusable ORM module; restore both to preserve the Round 3 filter. Standard responses are identical; the previous slower aggregate plan returns.
* Dashboard-only rollback: restore `dojo/home/views.py` and `dojo/utils.py` from Round 4. The existing Round 4 chart and punchcard improvements remain; the three exact counters again use a wide DISTINCT projection.

Rebuild the application image, verify its source SHA and restart only the application service. Never run `docker compose down -v`, drop databases/indices or replay migrations as a performance rollback. Benchmark middleware is removed from the final local serving configuration. Port 8080 and unrelated application/Engagement/UI branches remain separate.
