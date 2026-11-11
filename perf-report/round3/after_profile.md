141 objects imported automatically (use -v 2 for details).

{"actor": "admin", "url": "/api/v2/findings/?limit=100", "status": 200, "bytes": 283879, "wall_ms": 1314.095877998625, "sql_count": 24, "sql_ms": 114.86436502309516, "serializer": {"get_request_response": 23.56235499610193, "get_accepted_risks": 15.328804052842315, "get_jira_creation": 3.749746043467894, "get_jira_change": 1.558934964123182, "to_representation": 163.88421699230094}, "count": 1000168, "rows": 100}
## admin / /api/v2/findings/?limit=100 / 70.47 ms
SELECT <projection> FROM "dojo_finding"
Finalize Aggregate  (cost=17629.23..17629.24 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=4408
  ->  Gather  (cost=17629.01..17629.22 rows=2 width=8) (actual rows=3.00 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=4408
        ->  Partial Aggregate  (cost=16629.01..16629.02 rows=1 width=8) (actual rows=1.00 loops=3)
              Buffers: shared hit=4408
              ->  Parallel Index Only Scan using dojo_findin_duplica_f60788_idx on dojo_finding  (cost=0.42..15587.93 rows=416432 width=0) (actual rows=333389.33 loops=3)
                    Heap Fetches: 28247
                    Index Searches: 1
                    Buffers: shared hit=4408
Planning:
  Buffers: shared hit=4
Planning Time: 0.730 ms
Execution Time: 92.181 ms
## admin / /api/v2/findings/?limit=100 / 4.86 ms
SELECT <projection> FROM "dojo_test_type" INNER JOIN "dojo_finding_found_by" ON ("dojo_test_type"."id" = "dojo_finding_found_by"."test_type_id") WHERE "dojo_finding_found_by"."finding_id" IN (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ORDER BY "dojo_test_type"."name" ASC
Sort  (cost=10.31..10.56 rows=100 width=30) (actual rows=0.00 loops=1)
  Sort Key: dojo_test_type.name
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=1
  ->  Nested Loop  (cost=0.41..6.99 rows=100 width=30) (actual rows=0.00 loops=1)
        Buffers: shared hit=1
        ->  Seq Scan on dojo_finding_found_by  (cost=0.25..3.77 rows=100 width=8) (actual rows=0.00 loops=1)
              Filter: (finding_id = ANY ('?'::integer[]))
              Rows Removed by Filter: 168
              Buffers: shared hit=1
        ->  Memoize  (cost=0.16..0.38 rows=1 width=26) (never executed)
              Cache Key: dojo_finding_found_by.test_type_id
              Cache Mode: logical
              ->  Index Scan using dojo_test_type_pkey on dojo_test_type  (cost=0.15..0.36 rows=1 width=26) (never executed)
                    Index Cond: (id = dojo_finding_found_by.test_type_id)
                    Index Searches: 0
Planning:
  Buffers: shared hit=4
Planning Time: 0.378 ms
Execution Time: 0.085 ms
## admin / /api/v2/findings/?limit=100 / 3.55 ms
SELECT <projection> FROM "dojo_finding" ORDER BY "dojo_finding"."id" ASC LIMIT 100
Limit  (cost=0.42..15.55 rows=100 width=5463) (actual rows=100.00 loops=1)
  Buffers: shared hit=17
  ->  Index Scan using dojo_finding_pkey on dojo_finding  (cost=0.42..151168.53 rows=999437 width=5463) (actual rows=100.00 loops=1)
        Index Searches: 1
        Buffers: shared hit=17
Planning:
  Buffers: shared hit=2
Planning Time: 0.362 ms
Execution Time: 0.196 ms
{"actor": "heavy_member", "url": "/api/v2/findings/?limit=100", "status": 200, "bytes": 289442, "wall_ms": 449.3853809981374, "sql_count": 25, "sql_ms": 169.40328399505233, "serializer": {"get_request_response": 16.90127604524605, "get_accepted_risks": 20.478280988754705, "get_jira_creation": 2.2210689858184196, "get_jira_change": 0.6392509822035208, "to_representation": 123.47878902073717}, "count": 633794, "rows": 100}
## heavy_member / /api/v2/findings/?limit=100 / 136.70 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE "dojo_engagement"."product_id" IN (SELECT U0."id" AS "id" FROM "dojo_product" U0 LEFT OUTER JOIN "dojo_product_authorized_users" U1 ON (U0."id" = U1."product_id") INNER JOIN "dojo_product_type" U3 ON (U0."prod_type_id" = U3."id") LEFT OUTER JOIN "dojo_product_type_authorized_users" U4 ON (U3."id" = U4."product_type_id") WHERE (U1."dojo_user_id" = %s OR U4."dojo_user_id" = %s))
Finalize Aggregate  (cost=32196.05..32196.06 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=25997
  ->  Gather  (cost=32195.83..32196.04 rows=2 width=8) (actual rows=3.00 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=25997
        ->  Partial Aggregate  (cost=31195.83..31195.84 rows=1 width=8) (actual rows=1.00 loops=3)
              Buffers: shared hit=25997
              ->  Hash Join  (cost=133.01..30154.75 rows=416432 width=0) (actual rows=211264.67 loops=3)
                    Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
                    Buffers: shared hit=25997
                    ->  Hash Join  (cost=4.58..26729.57 rows=416432 width=4) (actual rows=333389.33 loops=3)
                          Hash Cond: (dojo_finding.test_id = dojo_test.id)
                          Buffers: shared hit=25424
                          ->  Parallel Index Only Scan using dojo_finding_test_id_ef8ec5fc on dojo_finding  (cost=0.42..25584.02 rows=416432 width=4) (actual rows=333389.33 loops=3)
                                Heap Fetches: 28163
                                Index Searches: 1
                                Buffers: shared hit=25376
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
Planning Time: 3.271 ms
Execution Time: 169.941 ms
## heavy_member / /api/v2/findings/?limit=100 / 4.02 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE "dojo_engagement"."product_id" IN (SELECT U0."id" AS "id" FROM "dojo_product" U0 LEFT OUTER JOIN "dojo_product_authorized_users" U1 ON (U0."id" = U1."product_id") INNER JOIN "dojo_product_type" U3 ON (U0."prod_type_id" = U3."id") LEFT OUTER JOIN "dojo_product_type_authorized_users" U4 ON (U3."id" = U4."product_type_id") WHERE (U1."dojo_user_id" = %s OR U4."dojo_user_id" = %s)) ORDER BY "dojo_finding"."id" ASC LIMIT 100
Limit  (cost=1.17..33.79 rows=100 width=5463) (actual rows=100.00 loops=1)
  Buffers: shared hit=313
  ->  Nested Loop  (cost=1.17..326060.89 rows=999437 width=5463) (actual rows=100.00 loops=1)
        Join Filter: (dojo_engagement.id = dojo_test.engagement_id)
        Rows Removed by Join Filter: 202
        Buffers: shared hit=313
        ->  Nested Loop  (cost=0.58..176017.01 rows=999437 width=5467) (actual rows=151.00 loops=1)
              Buffers: shared hit=124
              ->  Index Scan using dojo_finding_pkey on dojo_finding  (cost=0.42..151168.53 rows=999437 width=5463) (actual rows=151.00 loops=1)
                    Index Searches: 1
                    Buffers: shared hit=26
              ->  Memoize  (cost=0.15..0.17 rows=1 width=8) (actual rows=1.00 loops=151)
                    Cache Key: dojo_finding.test_id
                    Cache Mode: logical
                    Hits: 102  Misses: 49  Evictions: 0  Overflows: 0  Memory Usage: 6kB
                    Buffers: shared hit=98
                    ->  Index Scan using dojo_test_pkey on dojo_test  (cost=0.14..0.16 rows=1 width=8) (actual rows=1.00 loops=49)
                          Index Cond: (id = dojo_finding.test_id)
                          Index Searches: 49
                          Buffers: shared hit=98
        ->  Materialize  (cost=0.59..128.35 rows=10 width=4) (actual rows=2.00 loops=151)
              Storage: Memory  Maximum Storage: 17kB
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
  Buffers: shared hit=14
Planning Time: 1.569 ms
Execution Time: 0.655 ms
         534719 function calls (516960 primitive calls) in 0.913 seconds

   Ordered by: cumulative time
   List reduced from 1484 to 32 due to restriction <32>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.000    0.000    0.914    0.914 client.py:1113(get)
        1    0.000    0.000    0.914    0.914 client.py:467(get)
        1    0.000    0.000    0.914    0.914 client.py:633(generic)
        1    0.000    0.000    0.914    0.914 client.py:1066(request)
        1    0.000    0.000    0.913    0.913 client.py:169(__call__)
        1    0.000    0.000    0.913    0.913 base.py:136(get_response)
     23/1    0.000    0.000    0.913    0.913 exception.py:52(inner)
     10/1    0.000    0.000    0.913    0.913 deprecation.py:113(__call__)
        1    0.000    0.000    0.912    0.912 middleware.py:246(__call__)
        1    0.000    0.000    0.912    0.912 middleware.py:180(__call__)
        1    0.000    0.000    0.908    0.908 __init__.py:164(__call__)
        1    0.000    0.000    0.908    0.908 middleware.py:309(__call__)
        1    0.000    0.000    0.908    0.908 middleware.py:33(__call__)
        1    0.000    0.000    0.908    0.908 middleware.py:93(__call__)
        1    0.000    0.000    0.907    0.907 middleware.py:142(__call__)
        1    0.000    0.000    0.907    0.907 middleware.py:266(__call__)
        1    0.000    0.000    0.907    0.907 middleware.py:60(__call__)
        1    0.000    0.000    0.907    0.907 __init__.py:94(__call__)
        1    0.000    0.000    0.907    0.907 middleware.py:16(__call__)
        1    0.000    0.000    0.906    0.906 middleware.py:360(__call__)
        1    0.000    0.000    0.906    0.906 base.py:174(_get_response)
        1    0.000    0.000    0.900    0.900 csrf.py:64(_view_wrapper)
        1    0.000    0.000    0.900    0.900 viewsets.py:102(view)
        1    0.000    0.000    0.900    0.900 views.py:490(dispatch)
        1    0.000    0.000    0.890    0.890 drainage.py:205(wrapped_method)
        1    0.000    0.000    0.890    0.890 mixins.py:8(list)
        1    0.000    0.000    0.459    0.459 generics.py:169(paginate_queryset)
        1    0.000    0.000    0.459    0.459 large_offset_pagination.py:12(paginate_queryset)
        1    0.000    0.000    0.459    0.459 pagination.py:349(paginate_queryset)
  881/851    0.001    0.000    0.355    0.000 {method 'extend' of 'list' objects}
      101    0.000    0.000    0.354    0.004 mixins.py:23(<genexpr>)
  200/100    0.028    0.000    0.354    0.004 serializers.py:530(to_representation)


{"actor": "small_member", "url": "/api/v2/findings/?limit=100", "status": 200, "bytes": 294204, "wall_ms": 397.72549500048626, "sql_count": 25, "sql_ms": 146.4131019965862, "serializer": {"get_request_response": 16.945110037340783, "get_accepted_risks": 14.907630975358188, "get_jira_creation": 1.4365960087161511, "get_jira_change": 0.624259962933138, "to_representation": 94.87600901775295}, "count": 33684, "rows": 100}
## small_member / /api/v2/findings/?limit=100 / 107.58 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE "dojo_engagement"."product_id" IN (SELECT U0."id" AS "id" FROM "dojo_product" U0 LEFT OUTER JOIN "dojo_product_authorized_users" U1 ON (U0."id" = U1."product_id") INNER JOIN "dojo_product_type" U3 ON (U0."prod_type_id" = U3."id") LEFT OUTER JOIN "dojo_product_type_authorized_users" U4 ON (U3."id" = U4."product_type_id") WHERE (U1."dojo_user_id" = %s OR U4."dojo_user_id" = %s))
Finalize Aggregate  (cost=32196.05..32196.06 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=25982
  ->  Gather  (cost=32195.83..32196.04 rows=2 width=8) (actual rows=3.00 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=25982
        ->  Partial Aggregate  (cost=31195.83..31195.84 rows=1 width=8) (actual rows=1.00 loops=3)
              Buffers: shared hit=25982
              ->  Hash Join  (cost=133.01..30154.75 rows=416432 width=0) (actual rows=11228.00 loops=3)
                    Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
                    Buffers: shared hit=25982
                    ->  Hash Join  (cost=4.58..26729.57 rows=416432 width=4) (actual rows=333389.33 loops=3)
                          Hash Cond: (dojo_finding.test_id = dojo_test.id)
                          Buffers: shared hit=25409
                          ->  Parallel Index Only Scan using dojo_finding_test_id_ef8ec5fc on dojo_finding  (cost=0.42..25584.02 rows=416432 width=4) (actual rows=333389.33 loops=3)
                                Heap Fetches: 28163
                                Index Searches: 1
                                Buffers: shared hit=25361
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
Planning Time: 1.467 ms
Execution Time: 125.056 ms
## small_member / /api/v2/findings/?limit=100 / 15.58 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE "dojo_engagement"."product_id" IN (SELECT U0."id" AS "id" FROM "dojo_product" U0 LEFT OUTER JOIN "dojo_product_authorized_users" U1 ON (U0."id" = U1."product_id") INNER JOIN "dojo_product_type" U3 ON (U0."prod_type_id" = U3."id") LEFT OUTER JOIN "dojo_product_type_authorized_users" U4 ON (U3."id" = U4."product_type_id") WHERE (U1."dojo_user_id" = %s OR U4."dojo_user_id" = %s)) ORDER BY "dojo_finding"."id" ASC LIMIT 100
Limit  (cost=1.17..33.79 rows=100 width=5463) (actual rows=100.00 loops=1)
  Buffers: shared hit=784
  ->  Nested Loop  (cost=1.17..326060.89 rows=999437 width=5463) (actual rows=100.00 loops=1)
        Join Filter: (dojo_engagement.id = dojo_test.engagement_id)
        Rows Removed by Join Filter: 5094
        Buffers: shared hit=784
        ->  Nested Loop  (cost=0.58..176017.01 rows=999437 width=5467) (actual rows=2597.00 loops=1)
              Buffers: shared hit=595
              ->  Index Scan using dojo_finding_pkey on dojo_finding  (cost=0.42..151168.53 rows=999437 width=5463) (actual rows=2597.00 loops=1)
                    Index Searches: 1
                    Buffers: shared hit=403
              ->  Memoize  (cost=0.15..0.17 rows=1 width=8) (actual rows=1.00 loops=2597)
                    Cache Key: dojo_finding.test_id
                    Cache Mode: logical
                    Hits: 2501  Misses: 96  Evictions: 0  Overflows: 0  Memory Usage: 11kB
                    Buffers: shared hit=192
                    ->  Index Scan using dojo_test_pkey on dojo_test  (cost=0.14..0.16 rows=1 width=8) (actual rows=1.00 loops=96)
                          Index Cond: (id = dojo_finding.test_id)
                          Index Searches: 96
                          Buffers: shared hit=192
        ->  Materialize  (cost=0.59..128.35 rows=10 width=4) (actual rows=2.00 loops=2597)
              Storage: Memory  Maximum Storage: 17kB
              Buffers: shared hit=189
              ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=1)
                    Buffers: shared hit=189
                    ->  Seq Scan on dojo_engagement  (cost=0.00..10.10 rows=10 width=8) (actual rows=26.00 loops=1)
                          Buffers: shared hit=1
                    ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=26)
                          Filter: ((u1.dojo_user_id = 3) OR (u4.dojo_user_id = 3))
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
  Buffers: shared hit=14
Planning Time: 2.525 ms
Execution Time: 6.905 ms
{"actor": "heavy_member", "url": "/api/v2/findings/?product=2&severity=High&active=true&limit=100", "status": 200, "bytes": 288064, "wall_ms": 979.178604997287, "sql_count": 25, "sql_ms": 730.6376629931037, "serializer": {"get_request_response": 9.073560016986448, "get_accepted_risks": 10.527080965403002, "get_jira_creation": 0.8885130009730347, "get_jira_change": 0.571167009184137, "to_representation": 62.52717796451179}, "count": 63688, "rows": 100}
## heavy_member / /api/v2/findings/?product=2&severity=High&active=true&limit=100 / 700.83 ms
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
Planning Time: 1.325 ms
Execution Time: 301.362 ms
## heavy_member / /api/v2/findings/?product=2&severity=High&active=true&limit=100 / 7.56 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_engagement"."product_id" IN (SELECT U0."id" AS "id" FROM "dojo_product" U0 LEFT OUTER JOIN "dojo_product_authorized_users" U1 ON (U0."id" = U1."product_id") INNER JOIN "dojo_product_type" U3 ON (U0."prod_type_id" = U3."id") LEFT OUTER JOIN "dojo_product_type_authorized_users" U4 ON (U3."id" = U4."product_type_id") WHERE (U1."dojo_user_id" = %s OR U4."dojo_user_id" = %s)) AND "dojo_finding"."severity" IN (%s) AND "dojo_finding"."active" AND "dojo_finding"."test_id" = ANY((ARRAY(SELECT U0."id" AS "pk" FROM "dojo_test" U0 INNER JOIN "dojo_engagement" U1 ON (U0."engagement_id" = U1."id") WHERE U1."product_id" = %s)))) ORDER BY "dojo_finding"."id" ASC LIMIT 100
Limit  (cost=12.58..1745.74 rows=100 width=5463) (actual rows=100.00 loops=1)
  Buffers: shared hit=424 read=209
  InitPlan 1
    ->  Hash Join  (cost=8.16..11.42 rows=10 width=4) (actual rows=8.00 loops=1)
          Hash Cond: (u0_1.engagement_id = u1_1.id)
          Buffers: shared hit=2 read=2
          ->  Seq Scan on dojo_test u0_1  (cost=0.00..2.96 rows=96 width=8) (actual rows=100.00 loops=1)
                Buffers: shared hit=2
          ->  Hash  (cost=8.15..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                Buckets: 1024  Batches: 1  Memory Usage: 9kB
                Buffers: shared read=2
                ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement u1_1  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                      Index Cond: (product_id = 2)
                      Index Searches: 1
                      Buffers: shared read=2
  ->  Nested Loop  (cost=1.16..169331.22 rows=9770 width=5463) (actual rows=100.00 loops=1)
        Join Filter: (dojo_engagement.id = dojo_test.engagement_id)
        Rows Removed by Join Filter: 99
        Buffers: shared hit=424 read=209
        ->  Nested Loop  (cost=0.57..167737.40 rows=9770 width=5467) (actual rows=100.00 loops=1)
              Buffers: shared hit=239 read=205
              ->  Index Scan using dojo_finding_pkey on dojo_finding  (cost=0.42..166160.09 rows=9770 width=5463) (actual rows=100.00 loops=1)
                    Filter: (active AND ((severity)::text = '?'::text) AND (test_id = ANY ((InitPlan 1).col1)))
                    Rows Removed by Filter: 1454
                    Index Searches: 1
                    Buffers: shared hit=39 read=205
              ->  Index Scan using dojo_test_pkey on dojo_test  (cost=0.14..0.16 rows=1 width=8) (actual rows=1.00 loops=100)
                    Index Cond: (id = dojo_finding.test_id)
                    Index Searches: 100
                    Buffers: shared hit=200
        ->  Materialize  (cost=0.59..128.35 rows=10 width=4) (actual rows=1.99 loops=100)
              Storage: Memory  Maximum Storage: 17kB
              Buffers: shared hit=185 read=4
              ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=1)
                    Buffers: shared hit=185 read=4
                    ->  Seq Scan on dojo_engagement  (cost=0.00..10.10 rows=10 width=8) (actual rows=26.00 loops=1)
                          Buffers: shared hit=1
                    ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=26)
                          Filter: ((u1.dojo_user_id = 2) OR (u4.dojo_user_id = 2))
                          Rows Removed by Filter: 2
                          Buffers: shared hit=184 read=4
                          ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=26)
                                Buffers: shared hit=154 read=2
                                ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=26)
                                      Buffers: shared hit=102 read=2
                                      ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=26)
                                            Index Cond: (id = dojo_engagement.product_id)
                                            Index Searches: 26
                                            Buffers: shared hit=50 read=2
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
                                Buffers: shared hit=30 read=2
Planning:
  Buffers: shared hit=3 read=13
Planning Time: 1.202 ms
Execution Time: 1.752 ms
## heavy_member / /api/v2/findings/?product=2&severity=High&active=true&limit=100 / 2.26 ms
SELECT <projection> FROM "dojo_notes" INNER JOIN "dojo_finding_notes" ON ("dojo_notes"."id" = "dojo_finding_notes"."notes_id") LEFT OUTER JOIN "dojo_note_type" ON ("dojo_notes"."note_type_id" = "dojo_note_type"."id") INNER JOIN "auth_user" ON ("dojo_notes"."author_id" = "auth_user"."id") LEFT OUTER JOIN "auth_user" T6 ON ("dojo_notes"."editor_id" = T6."id") WHERE "dojo_finding_notes"."finding_id" IN (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ORDER BY "dojo_notes"."date" DESC
Sort  (cost=144.64..147.19 rows=1020 width=887) (actual rows=0.00 loops=1)
  Sort Key: dojo_notes.date DESC
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared read=2
  ->  Hash Left Join  (cost=57.48..93.67 rows=1020 width=887) (actual rows=0.00 loops=1)
        Hash Cond: (dojo_notes.editor_id = t6.id)
        Buffers: shared read=2
        ->  Hash Join  (cost=55.92..89.37 rows=1020 width=800) (actual rows=0.00 loops=1)
              Hash Cond: (dojo_notes.author_id = auth_user.id)
              Buffers: shared read=2
              ->  Hash Left Join  (cost=54.36..85.08 rows=1020 width=713) (actual rows=0.00 loops=1)
                    Hash Cond: (dojo_notes.note_type_id = dojo_note_type.id)
                    Buffers: shared read=1
                    ->  Hash Join  (cost=41.66..69.65 rows=1020 width=70) (actual rows=0.00 loops=1)
                          Hash Cond: (dojo_finding_notes.notes_id = dojo_notes.id)
                          Buffers: shared read=1
                          ->  Bitmap Heap Scan on dojo_finding_notes  (cost=12.31..37.61 rows=1020 width=8) (actual rows=0.00 loops=1)
                                Recheck Cond: (finding_id = ANY ('?'::integer[]))
                                Buffers: shared read=1
                                ->  Bitmap Index Scan on dojo_finding_notes_finding_id_701fd3e2  (cost=0.00..11.80 rows=1020 width=0) (actual rows=0.00 loops=1)
                                      Index Cond: (finding_id = ANY ('?'::integer[]))
                                      Index Searches: 1
                                      Buffers: shared read=1
                          ->  Hash  (cost=18.60..18.60 rows=860 width=66) (never executed)
                                ->  Seq Scan on dojo_notes  (cost=0.00..18.60 rows=860 width=66) (never executed)
                    ->  Hash  (cost=11.20..11.20 rows=120 width=643) (never executed)
                          ->  Seq Scan on dojo_note_type  (cost=0.00..11.20 rows=120 width=643) (never executed)
              ->  Hash  (cost=1.25..1.25 rows=25 width=87) (actual rows=25.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 12kB
                    Buffers: shared read=1
                    ->  Seq Scan on auth_user  (cost=0.00..1.25 rows=25 width=87) (actual rows=25.00 loops=1)
                          Buffers: shared read=1
        ->  Hash  (cost=1.25..1.25 rows=25 width=87) (never executed)
              ->  Seq Scan on auth_user t6  (cost=0.00..1.25 rows=25 width=87) (never executed)
Planning:
  Buffers: shared read=3
Planning Time: 0.419 ms
Execution Time: 0.154 ms
{"actor": "heavy_member", "url": "/api/v2/products/?findings=count", "status": 200, "bytes": 799, "wall_ms": 94.5920890007983, "sql_count": 10, "sql_ms": 77.11876199027756, "serializer": {}, "count": 1, "rows": 1}
## heavy_member / /api/v2/products/?findings=count / 59.75 ms
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
Planning Time: 0.575 ms
Execution Time: 88.390 ms
