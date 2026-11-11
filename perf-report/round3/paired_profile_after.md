141 objects imported automatically (use -v 2 for details).

{"actor": "admin", "url": "/api/v2/findings/?limit=100", "status": 200, "bytes": 283879, "wall_ms": 117.31016599514987, "sql_count": 24, "sql_ms": 18.313135995413177, "serializer": {"get_request_response": 2.8661469550570473, "get_accepted_risks": 1.5364279825007543, "get_jira_creation": 0.28129792190156877, "get_jira_change": 0.167124075233005, "to_representation": 17.547584997373633}, "count": 1000168, "rows": 100}
## admin / /api/v2/findings/?limit=100 / 13.31 ms
SELECT <projection> FROM "dojo_finding"
Finalize Aggregate  (cost=17629.23..17629.24 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=4410
  ->  Gather  (cost=17629.01..17629.22 rows=2 width=8) (actual rows=3.00 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=4410
        ->  Partial Aggregate  (cost=16629.01..16629.02 rows=1 width=8) (actual rows=1.00 loops=3)
              Buffers: shared hit=4410
              ->  Parallel Index Only Scan using dojo_findin_duplica_f60788_idx on dojo_finding  (cost=0.42..15587.93 rows=416432 width=0) (actual rows=333389.33 loops=3)
                    Heap Fetches: 28247
                    Index Searches: 1
                    Buffers: shared hit=4410
Planning:
  Buffers: shared hit=4
Planning Time: 0.100 ms
Execution Time: 13.505 ms
{"actor": "heavy_member", "url": "/api/v2/findings/?limit=100", "status": 200, "bytes": 289442, "wall_ms": 87.51323499018326, "sql_count": 25, "sql_ms": 37.36407101678196, "serializer": {"get_request_response": 2.829695018590428, "get_accepted_risks": 2.941318933153525, "get_jira_creation": 0.27962694002781063, "get_jira_change": 0.16541604418307543, "to_representation": 19.059064870816655}, "count": 633794, "rows": 100}
## heavy_member / /api/v2/findings/?limit=100 / 32.07 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE "dojo_engagement"."product_id" IN (SELECT U0."id" AS "id" FROM "dojo_product" U0 LEFT OUTER JOIN "dojo_product_authorized_users" U1 ON (U0."id" = U1."product_id") INNER JOIN "dojo_product_type" U3 ON (U0."prod_type_id" = U3."id") LEFT OUTER JOIN "dojo_product_type_authorized_users" U4 ON (U3."id" = U4."product_type_id") WHERE (U1."dojo_user_id" = %s OR U4."dojo_user_id" = %s))
Finalize Aggregate  (cost=32196.05..32196.06 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=26010
  ->  Gather  (cost=32195.83..32196.04 rows=2 width=8) (actual rows=3.00 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=26010
        ->  Partial Aggregate  (cost=31195.83..31195.84 rows=1 width=8) (actual rows=1.00 loops=3)
              Buffers: shared hit=26010
              ->  Hash Join  (cost=133.01..30154.75 rows=416432 width=0) (actual rows=211264.67 loops=3)
                    Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
                    Buffers: shared hit=26010
                    ->  Hash Join  (cost=4.58..26729.57 rows=416432 width=4) (actual rows=333389.33 loops=3)
                          Hash Cond: (dojo_finding.test_id = dojo_test.id)
                          Buffers: shared hit=25437
                          ->  Parallel Index Only Scan using dojo_finding_test_id_ef8ec5fc on dojo_finding  (cost=0.42..25584.02 rows=416432 width=4) (actual rows=333389.33 loops=3)
                                Heap Fetches: 28163
                                Index Searches: 1
                                Buffers: shared hit=25389
                          ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=100.00 loops=3)
                                Buckets: 1024  Batches: 1  Memory Usage: 12kB
                                Buffers: shared hit=48
                                ->  Seq Scan on dojo_test  (cost=0.00..2.96 rows=96 width=8) (actual rows=100.00 loops=3)
                                      Buffers: shared hit=48
                    ->  Hash  (cost=128.30..128.30 rows=10 width=4) (actual rows=2.00 loops=3)
                          Buckets: 1024  Batches: 1  Memory Usage: 9kB
                          Buffers: shared hit=573
                          ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=3)
                                Buffers: shared hit=573
                                ->  Seq Scan on dojo_engagement  (cost=0.00..10.10 rows=10 width=8) (actual rows=26.00 loops=3)
                                      Buffers: shared hit=3
                                ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=78)
                                      Filter: ((u1.dojo_user_id = 2) OR (u4.dojo_user_id = 2))
                                      Rows Removed by Filter: 2
                                      Buffers: shared hit=570
                                      ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=78)
                                            Buffers: shared hit=472
                                            ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=78)
                                                  Buffers: shared hit=316
                                                  ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=78)
                                                        Index Cond: (id = dojo_engagement.product_id)
                                                        Index Searches: 78
                                                        Buffers: shared hit=158
                                                  ->  Index Only Scan using dojo_product_type_pkey on dojo_product_type u3  (cost=0.14..0.96 rows=1 width=4) (actual rows=1.00 loops=78)
                                                        Index Cond: (id = u0.prod_type_id)
                                                        Heap Fetches: 78
                                                        Index Searches: 78
                                                        Buffers: shared hit=158
                                            ->  Index Scan using dojo_product_type_authorized_users_product_type_id_dba7ff5f on dojo_product_type_authorized_users u4  (cost=0.15..0.96 rows=10 width=8) (actual rows=0.00 loops=78)
                                                  Index Cond: (product_type_id = u3.id)
                                                  Index Searches: 78
                                                  Buffers: shared hit=156
                                      ->  Index Scan using dojo_product_authorized_users_product_id_ffcb106e on dojo_product_authorized_users u1  (cost=0.15..1.13 rows=10 width=8) (actual rows=1.31 loops=78)
                                            Index Cond: (product_id = u0.id)
                                            Index Searches: 78
                                            Buffers: shared hit=98
Planning:
  Buffers: shared hit=14
Planning Time: 0.319 ms
Execution Time: 40.098 ms
         534701 function calls (516942 primitive calls) in 0.175 seconds

   Ordered by: cumulative time
   List reduced from 1484 to 32 due to restriction <32>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.000    0.000    0.175    0.175 client.py:1113(get)
        1    0.000    0.000    0.175    0.175 client.py:467(get)
        1    0.000    0.000    0.175    0.175 client.py:633(generic)
        1    0.000    0.000    0.175    0.175 client.py:1066(request)
        1    0.000    0.000    0.175    0.175 client.py:169(__call__)
        1    0.000    0.000    0.175    0.175 base.py:136(get_response)
     23/1    0.000    0.000    0.175    0.175 exception.py:52(inner)
     10/1    0.000    0.000    0.175    0.175 deprecation.py:113(__call__)
        1    0.000    0.000    0.175    0.175 middleware.py:246(__call__)
        1    0.000    0.000    0.175    0.175 middleware.py:180(__call__)
        1    0.000    0.000    0.173    0.173 __init__.py:164(__call__)
        1    0.000    0.000    0.173    0.173 middleware.py:309(__call__)
        1    0.000    0.000    0.173    0.173 middleware.py:33(__call__)
        1    0.000    0.000    0.173    0.173 middleware.py:93(__call__)
        1    0.000    0.000    0.173    0.173 middleware.py:142(__call__)
        1    0.000    0.000    0.173    0.173 middleware.py:266(__call__)
        1    0.000    0.000    0.173    0.173 middleware.py:60(__call__)
        1    0.000    0.000    0.173    0.173 __init__.py:94(__call__)
        1    0.000    0.000    0.173    0.173 middleware.py:16(__call__)
        1    0.000    0.000    0.173    0.173 middleware.py:360(__call__)
        1    0.000    0.000    0.173    0.173 base.py:174(_get_response)
        1    0.000    0.000    0.171    0.171 csrf.py:64(_view_wrapper)
        1    0.000    0.000    0.171    0.171 viewsets.py:102(view)
        1    0.000    0.000    0.171    0.171 views.py:490(dispatch)
        1    0.000    0.000    0.170    0.170 drainage.py:205(wrapped_method)
        1    0.000    0.000    0.170    0.170 mixins.py:8(list)
        1    0.000    0.000    0.100    0.100 generics.py:169(paginate_queryset)
        1    0.000    0.000    0.100    0.100 large_offset_pagination.py:12(paginate_queryset)
        1    0.000    0.000    0.100    0.100 pagination.py:349(paginate_queryset)
1354/1307    0.000    0.000    0.069    0.000 query.py:1952(_fetch_all)
1229/1202    0.000    0.000    0.068    0.000 query.py:371(__iter__)
        1    0.000    0.000    0.058    0.058 query.py:1328(_prefetch_related_objects)


{"actor": "small_member", "url": "/api/v2/findings/?limit=100", "status": 200, "bytes": 294204, "wall_ms": 82.61769800446928, "sql_count": 25, "sql_ms": 30.721521019586362, "serializer": {"get_request_response": 3.469779054285027, "get_accepted_risks": 2.9951480246381834, "get_jira_creation": 0.2945910964626819, "get_jira_change": 0.16633990162517875, "to_representation": 19.850321958074346}, "count": 33684, "rows": 100}
## small_member / /api/v2/findings/?limit=100 / 24.36 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE "dojo_engagement"."product_id" IN (SELECT U0."id" AS "id" FROM "dojo_product" U0 LEFT OUTER JOIN "dojo_product_authorized_users" U1 ON (U0."id" = U1."product_id") INNER JOIN "dojo_product_type" U3 ON (U0."prod_type_id" = U3."id") LEFT OUTER JOIN "dojo_product_type_authorized_users" U4 ON (U3."id" = U4."product_type_id") WHERE (U1."dojo_user_id" = %s OR U4."dojo_user_id" = %s))
Finalize Aggregate  (cost=32196.05..32196.06 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=26012
  ->  Gather  (cost=32195.83..32196.04 rows=2 width=8) (actual rows=3.00 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=26012
        ->  Partial Aggregate  (cost=31195.83..31195.84 rows=1 width=8) (actual rows=1.00 loops=3)
              Buffers: shared hit=26012
              ->  Hash Join  (cost=133.01..30154.75 rows=416432 width=0) (actual rows=11228.00 loops=3)
                    Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
                    Buffers: shared hit=26012
                    ->  Hash Join  (cost=4.58..26729.57 rows=416432 width=4) (actual rows=333389.33 loops=3)
                          Hash Cond: (dojo_finding.test_id = dojo_test.id)
                          Buffers: shared hit=25439
                          ->  Parallel Index Only Scan using dojo_finding_test_id_ef8ec5fc on dojo_finding  (cost=0.42..25584.02 rows=416432 width=4) (actual rows=333389.33 loops=3)
                                Heap Fetches: 28163
                                Index Searches: 1
                                Buffers: shared hit=25391
                          ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=100.00 loops=3)
                                Buckets: 1024  Batches: 1  Memory Usage: 12kB
                                Buffers: shared hit=48
                                ->  Seq Scan on dojo_test  (cost=0.00..2.96 rows=96 width=8) (actual rows=100.00 loops=3)
                                      Buffers: shared hit=48
                    ->  Hash  (cost=128.30..128.30 rows=10 width=4) (actual rows=2.00 loops=3)
                          Buckets: 1024  Batches: 1  Memory Usage: 9kB
                          Buffers: shared hit=573
                          ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=3)
                                Buffers: shared hit=573
                                ->  Seq Scan on dojo_engagement  (cost=0.00..10.10 rows=10 width=8) (actual rows=26.00 loops=3)
                                      Buffers: shared hit=3
                                ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=78)
                                      Filter: ((u1.dojo_user_id = 3) OR (u4.dojo_user_id = 3))
                                      Rows Removed by Filter: 2
                                      Buffers: shared hit=570
                                      ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=78)
                                            Buffers: shared hit=472
                                            ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=78)
                                                  Buffers: shared hit=316
                                                  ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=78)
                                                        Index Cond: (id = dojo_engagement.product_id)
                                                        Index Searches: 78
                                                        Buffers: shared hit=158
                                                  ->  Index Only Scan using dojo_product_type_pkey on dojo_product_type u3  (cost=0.14..0.96 rows=1 width=4) (actual rows=1.00 loops=78)
                                                        Index Cond: (id = u0.prod_type_id)
                                                        Heap Fetches: 78
                                                        Index Searches: 78
                                                        Buffers: shared hit=158
                                            ->  Index Scan using dojo_product_type_authorized_users_product_type_id_dba7ff5f on dojo_product_type_authorized_users u4  (cost=0.15..0.96 rows=10 width=8) (actual rows=0.00 loops=78)
                                                  Index Cond: (product_type_id = u3.id)
                                                  Index Searches: 78
                                                  Buffers: shared hit=156
                                      ->  Index Scan using dojo_product_authorized_users_product_id_ffcb106e on dojo_product_authorized_users u1  (cost=0.15..1.13 rows=10 width=8) (actual rows=1.31 loops=78)
                                            Index Cond: (product_id = u0.id)
                                            Index Searches: 78
                                            Buffers: shared hit=98
Planning:
  Buffers: shared hit=14
Planning Time: 0.308 ms
Execution Time: 31.154 ms
{"actor": "heavy_member", "url": "/api/v2/findings/?product=2&severity=High&active=true&limit=100", "status": 200, "bytes": 288065, "wall_ms": 179.16804199921899, "sql_count": 25, "sql_ms": 130.09021795005538, "serializer": {"get_request_response": 2.779603935778141, "get_accepted_risks": 2.8417680150596425, "get_jira_creation": 0.27895811945199966, "get_jira_change": 0.1610430481377989, "to_representation": 18.686684939893894}, "count": 63688, "rows": 100}
## heavy_member / /api/v2/findings/?product=2&severity=High&active=true&limit=100 / 123.44 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_engagement"."product_id" IN (SELECT U0."id" AS "id" FROM "dojo_product" U0 LEFT OUTER JOIN "dojo_product_authorized_users" U1 ON (U0."id" = U1."product_id") INNER JOIN "dojo_product_type" U3 ON (U0."prod_type_id" = U3."id") LEFT OUTER JOIN "dojo_product_type_authorized_users" U4 ON (U3."id" = U4."product_type_id") WHERE (U1."dojo_user_id" = %s OR U4."dojo_user_id" = %s)) AND "dojo_finding"."severity" IN (%s) AND "dojo_finding"."active" AND "dojo_finding"."test_id" = ANY((ARRAY(SELECT U0."id" AS "pk" FROM "dojo_test" U0 INNER JOIN "dojo_engagement" U1 ON (U0."engagement_id" = U1."id") WHERE U1."product_id" = %s))))
Aggregate  (cost=32552.65..32552.66 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=301 read=66161
  InitPlan 1
    ->  Hash Join  (cost=8.16..11.42 rows=10 width=4) (actual rows=8.00 loops=1)
          Hash Cond: (u0_1.engagement_id = u1_1.id)
          Buffers: shared hit=4
          ->  Seq Scan on dojo_test u0_1  (cost=0.00..2.96 rows=96 width=8) (actual rows=100.00 loops=1)
                Buffers: shared hit=2
          ->  Hash  (cost=8.15..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                Buckets: 1024  Batches: 1  Memory Usage: 9kB
                Buffers: shared hit=2
                ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement u1_1  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                      Index Cond: (product_id = 2)
                      Index Searches: 1
                      Buffers: shared hit=2
  ->  Hash Join  (cost=2284.63..32516.80 rows=9770 width=0) (actual rows=63688.00 loops=1)
        Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
        Buffers: shared hit=301 read=66161
        ->  Hash Join  (cost=2156.20..32311.02 rows=9770 width=4) (actual rows=63688.00 loops=1)
              Hash Cond: (dojo_finding.test_id = dojo_test.id)
              Buffers: shared hit=112 read=66161
              ->  Bitmap Heap Scan on dojo_finding  (cost=2152.04..32280.08 rows=9770 width=4) (actual rows=63688.00 loops=1)
                    Recheck Cond: (((severity)::text = '?'::text) AND active AND (test_id = ANY ((InitPlan 1).col1)))
                    Rows Removed by Index Recheck: 247279
                    Heap Blocks: exact=32484 lossy=33201
                    Buffers: shared hit=110 read=66161
                    ->  BitmapAnd  (cost=2152.04..2152.04 rows=9770 width=0) (actual rows=0.00 loops=1)
                          Buffers: shared hit=4 read=582
                          ->  Bitmap Index Scan on idx_finding_sev_active  (cost=0.00..1053.46 rows=98271 width=0) (actual rows=100279.00 loops=1)
                                Index Cond: ((severity)::text = '?'::text)
                                Index Searches: 1
                                Buffers: shared read=82
                          ->  Bitmap Index Scan on dojo_finding_test_id_ef8ec5fc  (cost=0.00..1093.45 rows=99361 width=0) (actual rows=633794.00 loops=1)
                                Index Cond: (test_id = ANY ((InitPlan 1).col1))
                                Index Searches: 1
                                Buffers: shared hit=4 read=500
              ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=100.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 12kB
                    Buffers: shared hit=2
                    ->  Seq Scan on dojo_test  (cost=0.00..2.96 rows=96 width=8) (actual rows=100.00 loops=1)
                          Buffers: shared hit=2
        ->  Hash  (cost=128.30..128.30 rows=10 width=4) (actual rows=2.00 loops=1)
              Buckets: 1024  Batches: 1  Memory Usage: 9kB
              Buffers: shared hit=189
              ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=1)
                    Buffers: shared hit=189
                    ->  Seq Scan on dojo_engagement  (cost=0.00..10.10 rows=10 width=8) (actual rows=26.00 loops=1)
                          Buffers: shared hit=1
                    ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=26)
                          Filter: ((u1.dojo_user_id = 2) OR (u4.dojo_user_id = 2))
                          Rows Removed by Filter: 2
                          Buffers: shared hit=188
                          ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=26)
                                Buffers: shared hit=156
                                ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=26)
                                      Buffers: shared hit=104
                                      ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=26)
                                            Index Cond: (id = dojo_engagement.product_id)
                                            Index Searches: 26
                                            Buffers: shared hit=52
                                      ->  Index Only Scan using dojo_product_type_pkey on dojo_product_type u3  (cost=0.14..0.96 rows=1 width=4) (actual rows=1.00 loops=26)
                                            Index Cond: (id = u0.prod_type_id)
                                            Heap Fetches: 26
                                            Index Searches: 26
                                            Buffers: shared hit=52
                                ->  Index Scan using dojo_product_type_authorized_users_product_type_id_dba7ff5f on dojo_product_type_authorized_users u4  (cost=0.15..0.96 rows=10 width=8) (actual rows=0.00 loops=26)
                                      Index Cond: (product_type_id = u3.id)
                                      Index Searches: 26
                                      Buffers: shared hit=52
                          ->  Index Scan using dojo_product_authorized_users_product_id_ffcb106e on dojo_product_authorized_users u1  (cost=0.15..1.13 rows=10 width=8) (actual rows=1.31 loops=26)
                                Index Cond: (product_id = u0.id)
                                Index Searches: 26
                                Buffers: shared hit=32
Planning:
  Buffers: shared hit=16
Planning Time: 0.430 ms
Execution Time: 125.823 ms
{"actor": "heavy_member", "url": "/api/v2/products/?findings=count", "status": 200, "bytes": 799, "wall_ms": 29.031799000222236, "sql_count": 10, "sql_ms": 23.598801039042883, "serializer": {}, "count": 1, "rows": 1}
## heavy_member / /api/v2/products/?findings=count / 17.66 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_finding"."active" AND "dojo_engagement"."product_id" IN (%s)) GROUP BY 1
GroupAggregate  (cost=0.70..4460.11 rows=1 width=12) (actual rows=1.00 loops=1)
  Buffers: shared hit=13852
  ->  Nested Loop  (cost=0.70..4250.77 rows=83730 width=4) (actual rows=532569.00 loops=1)
        Buffers: shared hit=13852
        ->  Nested Loop  (cost=0.28..24.18 rows=10 width=8) (actual rows=8.00 loops=1)
              Join Filter: (dojo_engagement.id = dojo_test.engagement_id)
              Rows Removed by Join Filter: 188
              Buffers: shared hit=5
              ->  Index Scan using dojo_test_pkey on dojo_test  (cost=0.14..14.58 rows=96 width=8) (actual rows=100.00 loops=1)
                    Index Searches: 1
                    Buffers: shared hit=3
              ->  Materialize  (cost=0.14..8.16 rows=1 width=8) (actual rows=1.96 loops=100)
                    Storage: Memory  Maximum Storage: 17kB
                    Buffers: shared hit=2
                    ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                          Index Cond: (product_id = 2)
                          Index Searches: 1
                          Buffers: shared hit=2
        ->  Index Only Scan using dojo_findin_test_id_bfc47c_idx on dojo_finding  (cost=0.42..335.44 rows=8722 width=4) (actual rows=66571.12 loops=8)
              Index Cond: ((test_id = dojo_test.id) AND (active = true))
              Heap Fetches: 14924
              Index Searches: 8
              Buffers: shared hit=13847
Planning:
  Buffers: shared hit=8
Planning Time: 0.176 ms
Execution Time: 25.206 ms
