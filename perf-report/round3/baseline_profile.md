141 objects imported automatically (use -v 2 for details).

{"actor": "admin", "url": "/api/v2/findings/?limit=100", "status": 200, "bytes": 283879, "wall_ms": 111.93275199912023, "sql_count": 24, "sql_ms": 19.488222009385936, "serializer": {"get_request_response": 2.5951990246539935, "get_accepted_risks": 1.4265560457715765, "get_jira_creation": 0.26804599474417046, "get_jira_change": 0.15271292068064213, "to_representation": 16.326604010828305}, "count": 1000000, "rows": 100}
## admin / /api/v2/findings/?limit=100 / 14.69 ms
SELECT <projection> FROM "dojo_finding"
Finalize Aggregate  (cost=17617.23..17617.24 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=4072
  ->  Gather  (cost=17617.01..17617.22 rows=2 width=8) (actual rows=3.00 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=4072
        ->  Partial Aggregate  (cost=16617.01..16617.02 rows=1 width=8) (actual rows=1.00 loops=3)
              Buffers: shared hit=4072
              ->  Parallel Index Only Scan using dojo_finding_reporter_id_dec2fe8c on dojo_finding  (cost=0.42..15575.93 rows=416432 width=0) (actual rows=333333.33 loops=3)
                    Heap Fetches: 26055
                    Index Searches: 1
                    Buffers: shared hit=4072
Planning:
  Buffers: shared hit=4
Planning Time: 0.105 ms
Execution Time: 13.183 ms
{"actor": "heavy_member", "url": "/api/v2/findings/?limit=100", "status": 200, "bytes": 289442, "wall_ms": 81.01531099964632, "sql_count": 25, "sql_ms": 33.2444250016124, "serializer": {"get_request_response": 2.797584020299837, "get_accepted_risks": 2.8668289523920976, "get_jira_creation": 0.2800040238071233, "get_jira_change": 0.15421205171151087, "to_representation": 18.173123971791938}, "count": 633794, "rows": 100}
## heavy_member / /api/v2/findings/?limit=100 / 28.14 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE "dojo_engagement"."product_id" IN (SELECT U0."id" AS "id" FROM "dojo_product" U0 LEFT OUTER JOIN "dojo_product_authorized_users" U1 ON (U0."id" = U1."product_id") INNER JOIN "dojo_product_type" U3 ON (U0."prod_type_id" = U3."id") LEFT OUTER JOIN "dojo_product_type_authorized_users" U4 ON (U3."id" = U4."product_type_id") WHERE (U1."dojo_user_id" = %s OR U4."dojo_user_id" = %s))
Finalize Aggregate  (cost=32196.05..32196.06 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=24144
  ->  Gather  (cost=32195.83..32196.04 rows=2 width=8) (actual rows=3.00 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=24144
        ->  Partial Aggregate  (cost=31195.83..31195.84 rows=1 width=8) (actual rows=1.00 loops=3)
              Buffers: shared hit=24144
              ->  Hash Join  (cost=133.01..30154.75 rows=416432 width=0) (actual rows=211264.67 loops=3)
                    Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
                    Buffers: shared hit=24144
                    ->  Hash Join  (cost=4.58..26729.57 rows=416432 width=4) (actual rows=333333.33 loops=3)
                          Hash Cond: (dojo_finding.test_id = dojo_test.id)
                          Buffers: shared hit=23613
                          ->  Parallel Index Only Scan using dojo_finding_test_id_ef8ec5fc on dojo_finding  (cost=0.42..25584.02 rows=416432 width=4) (actual rows=333333.33 loops=3)
                                Heap Fetches: 26055
                                Index Searches: 1
                                Buffers: shared hit=23565
                          ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=3)
                                Buckets: 1024  Batches: 1  Memory Usage: 12kB
                                Buffers: shared hit=48
                                ->  Seq Scan on dojo_test  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=3)
                                      Buffers: shared hit=48
                    ->  Hash  (cost=128.30..128.30 rows=10 width=4) (actual rows=2.00 loops=3)
                          Buckets: 1024  Batches: 1  Memory Usage: 9kB
                          Buffers: shared hit=531
                          ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=3)
                                Buffers: shared hit=531
                                ->  Seq Scan on dojo_engagement  (cost=0.00..10.10 rows=10 width=8) (actual rows=24.00 loops=3)
                                      Buffers: shared hit=3
                                ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=72)
                                      Filter: ((u1.dojo_user_id = 2) OR (u4.dojo_user_id = 2))
                                      Rows Removed by Filter: 2
                                      Buffers: shared hit=528
                                      ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=72)
                                            Buffers: shared hit=436
                                            ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=72)
                                                  Buffers: shared hit=292
                                                  ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=72)
                                                        Index Cond: (id = dojo_engagement.product_id)
                                                        Index Searches: 72
                                                        Buffers: shared hit=146
                                                  ->  Index Only Scan using dojo_product_type_pkey on dojo_product_type u3  (cost=0.14..0.96 rows=1 width=4) (actual rows=1.00 loops=72)
                                                        Index Cond: (id = u0.prod_type_id)
                                                        Heap Fetches: 72
                                                        Index Searches: 72
                                                        Buffers: shared hit=146
                                            ->  Index Scan using dojo_product_type_authorized_users_product_type_id_dba7ff5f on dojo_product_type_authorized_users u4  (cost=0.15..0.96 rows=10 width=8) (actual rows=0.00 loops=72)
                                                  Index Cond: (product_type_id = u3.id)
                                                  Index Searches: 72
                                                  Buffers: shared hit=144
                                      ->  Index Scan using dojo_product_authorized_users_product_id_ffcb106e on dojo_product_authorized_users u1  (cost=0.15..1.13 rows=10 width=8) (actual rows=1.42 loops=72)
                                            Index Cond: (product_id = u0.id)
                                            Index Searches: 72
                                            Buffers: shared hit=92
Planning:
  Buffers: shared hit=14
Planning Time: 0.444 ms
Execution Time: 34.121 ms
         534619 function calls (516876 primitive calls) in 0.155 seconds

   Ordered by: cumulative time
   List reduced from 1484 to 32 due to restriction <32>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.000    0.000    0.155    0.155 client.py:1113(get)
        1    0.000    0.000    0.155    0.155 client.py:467(get)
        1    0.000    0.000    0.155    0.155 client.py:633(generic)
        1    0.000    0.000    0.155    0.155 client.py:1066(request)
        1    0.000    0.000    0.155    0.155 client.py:169(__call__)
        1    0.000    0.000    0.155    0.155 base.py:136(get_response)
     23/1    0.000    0.000    0.155    0.155 exception.py:52(inner)
     10/1    0.000    0.000    0.155    0.155 deprecation.py:113(__call__)
        1    0.000    0.000    0.155    0.155 middleware.py:246(__call__)
        1    0.000    0.000    0.155    0.155 middleware.py:180(__call__)
        1    0.000    0.000    0.154    0.154 __init__.py:164(__call__)
        1    0.000    0.000    0.154    0.154 middleware.py:309(__call__)
        1    0.000    0.000    0.153    0.153 middleware.py:33(__call__)
        1    0.000    0.000    0.153    0.153 middleware.py:93(__call__)
        1    0.000    0.000    0.153    0.153 middleware.py:142(__call__)
        1    0.000    0.000    0.153    0.153 middleware.py:266(__call__)
        1    0.000    0.000    0.153    0.153 middleware.py:60(__call__)
        1    0.000    0.000    0.153    0.153 __init__.py:94(__call__)
        1    0.000    0.000    0.153    0.153 middleware.py:16(__call__)
        1    0.000    0.000    0.153    0.153 middleware.py:360(__call__)
        1    0.000    0.000    0.153    0.153 base.py:174(_get_response)
        1    0.000    0.000    0.152    0.152 csrf.py:64(_view_wrapper)
        1    0.000    0.000    0.152    0.152 viewsets.py:102(view)
        1    0.000    0.000    0.152    0.152 views.py:490(dispatch)
        1    0.000    0.000    0.151    0.151 drainage.py:205(wrapped_method)
        1    0.000    0.000    0.151    0.151 mixins.py:8(list)
        1    0.000    0.000    0.088    0.088 generics.py:169(paginate_queryset)
        1    0.000    0.000    0.088    0.088 large_offset_pagination.py:12(paginate_queryset)
        1    0.000    0.000    0.088    0.088 pagination.py:349(paginate_queryset)
1354/1307    0.000    0.000    0.062    0.000 query.py:1952(_fetch_all)
1229/1202    0.000    0.000    0.061    0.000 query.py:371(__iter__)
        1    0.000    0.000    0.052    0.052 query.py:1328(_prefetch_related_objects)


{"actor": "small_member", "url": "/api/v2/findings/?limit=100", "status": 200, "bytes": 294204, "wall_ms": 80.66309899732005, "sql_count": 25, "sql_ms": 32.013163989176974, "serializer": {"get_request_response": 3.2814050573506393, "get_accepted_risks": 2.804321004077792, "get_jira_creation": 0.2812610036926344, "get_jira_change": 0.15495704428758472, "to_representation": 18.787684020935558}, "count": 33684, "rows": 100}
## small_member / /api/v2/findings/?limit=100 / 25.80 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE "dojo_engagement"."product_id" IN (SELECT U0."id" AS "id" FROM "dojo_product" U0 LEFT OUTER JOIN "dojo_product_authorized_users" U1 ON (U0."id" = U1."product_id") INNER JOIN "dojo_product_type" U3 ON (U0."prod_type_id" = U3."id") LEFT OUTER JOIN "dojo_product_type_authorized_users" U4 ON (U3."id" = U4."product_type_id") WHERE (U1."dojo_user_id" = %s OR U4."dojo_user_id" = %s))
Finalize Aggregate  (cost=32196.05..32196.06 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=24134
  ->  Gather  (cost=32195.83..32196.04 rows=2 width=8) (actual rows=3.00 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=24134
        ->  Partial Aggregate  (cost=31195.83..31195.84 rows=1 width=8) (actual rows=1.00 loops=3)
              Buffers: shared hit=24134
              ->  Hash Join  (cost=133.01..30154.75 rows=416432 width=0) (actual rows=11228.00 loops=3)
                    Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
                    Buffers: shared hit=24134
                    ->  Hash Join  (cost=4.58..26729.57 rows=416432 width=4) (actual rows=333333.33 loops=3)
                          Hash Cond: (dojo_finding.test_id = dojo_test.id)
                          Buffers: shared hit=23603
                          ->  Parallel Index Only Scan using dojo_finding_test_id_ef8ec5fc on dojo_finding  (cost=0.42..25584.02 rows=416432 width=4) (actual rows=333333.33 loops=3)
                                Heap Fetches: 26055
                                Index Searches: 1
                                Buffers: shared hit=23555
                          ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=3)
                                Buckets: 1024  Batches: 1  Memory Usage: 12kB
                                Buffers: shared hit=48
                                ->  Seq Scan on dojo_test  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=3)
                                      Buffers: shared hit=48
                    ->  Hash  (cost=128.30..128.30 rows=10 width=4) (actual rows=2.00 loops=3)
                          Buckets: 1024  Batches: 1  Memory Usage: 9kB
                          Buffers: shared hit=531
                          ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=3)
                                Buffers: shared hit=531
                                ->  Seq Scan on dojo_engagement  (cost=0.00..10.10 rows=10 width=8) (actual rows=24.00 loops=3)
                                      Buffers: shared hit=3
                                ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=72)
                                      Filter: ((u1.dojo_user_id = 3) OR (u4.dojo_user_id = 3))
                                      Rows Removed by Filter: 2
                                      Buffers: shared hit=528
                                      ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=72)
                                            Buffers: shared hit=436
                                            ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=72)
                                                  Buffers: shared hit=292
                                                  ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=72)
                                                        Index Cond: (id = dojo_engagement.product_id)
                                                        Index Searches: 72
                                                        Buffers: shared hit=146
                                                  ->  Index Only Scan using dojo_product_type_pkey on dojo_product_type u3  (cost=0.14..0.96 rows=1 width=4) (actual rows=1.00 loops=72)
                                                        Index Cond: (id = u0.prod_type_id)
                                                        Heap Fetches: 72
                                                        Index Searches: 72
                                                        Buffers: shared hit=146
                                            ->  Index Scan using dojo_product_type_authorized_users_product_type_id_dba7ff5f on dojo_product_type_authorized_users u4  (cost=0.15..0.96 rows=10 width=8) (actual rows=0.00 loops=72)
                                                  Index Cond: (product_type_id = u3.id)
                                                  Index Searches: 72
                                                  Buffers: shared hit=144
                                      ->  Index Scan using dojo_product_authorized_users_product_id_ffcb106e on dojo_product_authorized_users u1  (cost=0.15..1.13 rows=10 width=8) (actual rows=1.42 loops=72)
                                            Index Cond: (product_id = u0.id)
                                            Index Searches: 72
                                            Buffers: shared hit=92
Planning:
  Buffers: shared hit=14
Planning Time: 0.366 ms
Execution Time: 29.210 ms
{"actor": "heavy_member", "url": "/api/v2/findings/?product=2&severity=High&active=true&limit=100", "status": 200, "bytes": 288064, "wall_ms": 306.57908500143094, "sql_count": 25, "sql_ms": 258.11081897700205, "serializer": {"get_request_response": 2.673076953215059, "get_accepted_risks": 2.71119403623743, "get_jira_creation": 0.2720439588301815, "get_jira_change": 0.15654398157494143, "to_representation": 17.719539006066043}, "count": 63688, "rows": 100}
## heavy_member / /api/v2/findings/?product=2&severity=High&active=true&limit=100 / 252.01 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_engagement"."product_id" IN (SELECT U0."id" AS "id" FROM "dojo_product" U0 LEFT OUTER JOIN "dojo_product_authorized_users" U1 ON (U0."id" = U1."product_id") INNER JOIN "dojo_product_type" U3 ON (U0."prod_type_id" = U3."id") LEFT OUTER JOIN "dojo_product_type_authorized_users" U4 ON (U3."id" = U4."product_type_id") WHERE (U1."dojo_user_id" = %s OR U4."dojo_user_id" = %s)) AND "dojo_finding"."severity" IN (%s) AND "dojo_finding"."active" AND "dojo_engagement"."product_id" IN (%s))
Aggregate  (cost=39887.69..39887.70 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=64 read=162696
  ->  Nested Loop  (cost=1193.83..39862.10 rows=10237 width=0) (actual rows=63688.00 loops=1)
        Buffers: shared hit=64 read=162696
        ->  Nested Loop Semi Join  (cost=12.83..49.10 rows=10 width=4) (actual rows=8.00 loops=1)
              Buffers: shared hit=12
              ->  Hash Join  (cost=8.16..11.42 rows=10 width=8) (actual rows=8.00 loops=1)
                    Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
                    Buffers: shared hit=4
                    ->  Seq Scan on dojo_test  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                          Buffers: shared hit=2
                    ->  Hash  (cost=8.15..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                          Buckets: 1024  Batches: 1  Memory Usage: 9kB
                          Buffers: shared hit=2
                          ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                                Index Cond: (product_id = 2)
                                Index Searches: 1
                                Buffers: shared hit=2
              ->  Materialize  (cost=4.67..37.50 rows=3 width=4) (actual rows=1.00 loops=8)
                    Storage: Memory  Maximum Storage: 17kB
                    Buffers: shared hit=8
                    ->  Nested Loop Left Join  (cost=4.67..37.48 rows=3 width=4) (actual rows=1.00 loops=1)
                          Filter: ((u1.dojo_user_id = 2) OR (u4.dojo_user_id = 2))
                          Buffers: shared hit=8
                          ->  Nested Loop Left Join  (cost=0.44..17.60 rows=29 width=8) (actual rows=1.00 loops=1)
                                Buffers: shared hit=6
                                ->  Nested Loop  (cost=0.28..16.54 rows=1 width=8) (actual rows=1.00 loops=1)
                                      Buffers: shared hit=4
                                      ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..8.16 rows=1 width=8) (actual rows=1.00 loops=1)
                                            Index Cond: (id = 2)
                                            Index Searches: 1
                                            Buffers: shared hit=2
                                      ->  Index Only Scan using dojo_product_type_pkey on dojo_product_type u3  (cost=0.14..8.16 rows=1 width=4) (actual rows=1.00 loops=1)
                                            Index Cond: (id = u0.prod_type_id)
                                            Heap Fetches: 1
                                            Index Searches: 1
                                            Buffers: shared hit=2
                                ->  Index Scan using dojo_product_type_authorized_users_product_type_id_dba7ff5f on dojo_product_type_authorized_users u4  (cost=0.15..0.96 rows=10 width=8) (actual rows=0.00 loops=1)
                                      Index Cond: (product_type_id = u3.id)
                                      Index Searches: 1
                                      Buffers: shared hit=2
                          ->  Materialize  (cost=4.23..14.84 rows=10 width=8) (actual rows=1.00 loops=1)
                                Storage: Memory  Maximum Storage: 17kB
                                Buffers: shared hit=2
                                ->  Bitmap Heap Scan on dojo_product_authorized_users u1  (cost=4.23..14.79 rows=10 width=8) (actual rows=1.00 loops=1)
                                      Recheck Cond: (product_id = 2)
                                      Heap Blocks: exact=1
                                      Buffers: shared hit=2
                                      ->  Bitmap Index Scan on dojo_product_authorized_users_product_id_ffcb106e  (cost=0.00..4.23 rows=10 width=0) (actual rows=8.00 loops=1)
                                            Index Cond: (product_id = 2)
                                            Index Searches: 1
                                            Buffers: shared hit=1
        ->  Bitmap Heap Scan on dojo_finding  (cost=1181.00..3971.06 rows=1024 width=4) (actual rows=7961.00 loops=8)
              Recheck Cond: ((dojo_test.id = test_id) AND ((severity)::text = '?'::text) AND active)
              Rows Removed by Index Recheck: 17489
              Heap Blocks: exact=161586
              Buffers: shared hit=52 read=162696
              ->  BitmapAnd  (cost=1181.00..1181.00 rows=1024 width=0) (actual rows=0.00 loops=8)
                    Buffers: shared read=1162
                    ->  Bitmap Index Scan on dojo_finding_test_id_ef8ec5fc  (cost=0.00..102.47 rows=10411 width=0) (actual rows=79224.25 loops=8)
                          Index Cond: (test_id = dojo_test.id)
                          Index Searches: 8
                          Buffers: shared read=514
                    ->  Bitmap Index Scan on idx_finding_sev_active  (cost=0.00..1053.46 rows=98271 width=0) (actual rows=100225.00 loops=8)
                          Index Cond: ((severity)::text = '?'::text)
                          Index Searches: 8
                          Buffers: shared read=648
Planning:
  Buffers: shared hit=14
Planning Time: 0.324 ms
Execution Time: 253.780 ms
{"actor": "heavy_member", "url": "/api/v2/products/?findings=count", "status": 200, "bytes": 799, "wall_ms": 27.021645997592714, "sql_count": 10, "sql_ms": 22.02971398946829, "serializer": {}, "count": 1, "rows": 1}
## heavy_member / /api/v2/products/?findings=count / 16.28 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_finding"."active" AND "dojo_engagement"."product_id" IN (%s)) GROUP BY 1
GroupAggregate  (cost=0.70..4460.11 rows=1 width=12) (actual rows=1.00 loops=1)
  Buffers: shared hit=12926
  ->  Nested Loop  (cost=0.70..4250.77 rows=83730 width=4) (actual rows=532569.00 loops=1)
        Buffers: shared hit=12926
        ->  Nested Loop  (cost=0.28..24.18 rows=10 width=8) (actual rows=8.00 loops=1)
              Join Filter: (dojo_engagement.id = dojo_test.engagement_id)
              Rows Removed by Join Filter: 180
              Buffers: shared hit=5
              ->  Index Scan using dojo_test_pkey on dojo_test  (cost=0.14..14.58 rows=96 width=8) (actual rows=96.00 loops=1)
                    Index Searches: 1
                    Buffers: shared hit=3
              ->  Materialize  (cost=0.14..8.16 rows=1 width=8) (actual rows=1.96 loops=96)
                    Storage: Memory  Maximum Storage: 17kB
                    Buffers: shared hit=2
                    ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                          Index Cond: (product_id = 2)
                          Index Searches: 1
                          Buffers: shared hit=2
        ->  Index Only Scan using dojo_findin_test_id_bfc47c_idx on dojo_finding  (cost=0.42..335.44 rows=8722 width=4) (actual rows=66571.12 loops=8)
              Index Cond: ((test_id = dojo_test.id) AND (active = true))
              Heap Fetches: 13900
              Index Searches: 8
              Buffers: shared hit=12921
Planning:
  Buffers: shared hit=8
Planning Time: 0.147 ms
Execution Time: 23.240 ms
