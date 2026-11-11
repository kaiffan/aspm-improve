141 objects imported automatically (use -v 2 for details).

{"case": "baseline", "product": 2, "severity": false, "count": 633794, "count_ms": 43.775348996859975}
Finalize Aggregate  (cost=32196.05..32196.06 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=24119
  ->  Gather  (cost=32195.83..32196.04 rows=2 width=8) (actual rows=3.00 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=24119
        ->  Partial Aggregate  (cost=31195.83..31195.84 rows=1 width=8) (actual rows=1.00 loops=3)
              Buffers: shared hit=24119
              ->  Hash Join  (cost=133.01..30154.75 rows=416432 width=0) (actual rows=211264.67 loops=3)
                    Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
                    Buffers: shared hit=24119
                    ->  Hash Join  (cost=4.58..26729.57 rows=416432 width=4) (actual rows=333333.33 loops=3)
                          Hash Cond: (dojo_finding.test_id = dojo_test.id)
                          Buffers: shared hit=23588
                          ->  Parallel Index Only Scan using dojo_finding_test_id_ef8ec5fc on dojo_finding  (cost=0.42..25584.02 rows=416432 width=4) (actual rows=333333.33 loops=3)
                                Heap Fetches: 26055
                                Index Searches: 1
                                Buffers: shared hit=23540
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
Planning Time: 0.387 ms
Execution Time: 68.350 ms
{"case": "subquery", "product": 2, "severity": false, "count": 633794, "count_ms": 23.009383003227413}
Finalize Aggregate  (cost=32967.29..32967.30 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=13813
  ->  Gather  (cost=32967.08..32967.29 rows=2 width=8) (actual rows=3.00 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=13813
        ->  Partial Aggregate  (cost=31967.08..31967.09 rows=1 width=8) (actual rows=1.00 loops=3)
              Buffers: shared hit=13813
              ->  Merge Semi Join  (cost=136.52..30926.00 rows=416432 width=0) (actual rows=211264.67 loops=3)
                    Merge Cond: (dojo_finding.test_id = v0.id)
                    Buffers: shared hit=13813
                    ->  Parallel Index Only Scan using dojo_finding_test_id_ef8ec5fc on dojo_finding  (cost=0.42..25584.02 rows=416432 width=4) (actual rows=211265.67 loops=3)
                          Heap Fetches: 16538
                          Index Searches: 1
                          Buffers: shared hit=13226
                    ->  Sort  (cost=136.10..136.34 rows=96 width=4) (actual rows=8.00 loops=3)
                          Sort Key: v0.id
                          Sort Method: quicksort  Memory: 25kB
                          Buffers: shared hit=587
                          Worker 0:  Sort Method: quicksort  Memory: 25kB
                          Worker 1:  Sort Method: quicksort  Memory: 25kB
                          ->  Hash Join  (cost=4.75..132.94 rows=96 width=4) (actual rows=8.00 loops=3)
                                Hash Cond: (v1.id = v0.engagement_id)
                                Buffers: shared hit=579
                                ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=3)
                                      Buffers: shared hit=573
                                      ->  Seq Scan on dojo_engagement v1  (cost=0.00..10.10 rows=10 width=8) (actual rows=24.00 loops=3)
                                            Buffers: shared hit=45
                                      ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=72)
                                            Filter: ((u1.dojo_user_id = 2) OR (u4.dojo_user_id = 2))
                                            Rows Removed by Filter: 2
                                            Buffers: shared hit=528
                                            ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=72)
                                                  Buffers: shared hit=436
                                                  ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=72)
                                                        Buffers: shared hit=292
                                                        ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=72)
                                                              Index Cond: (id = v1.product_id)
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
                                ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=3)
                                      Buckets: 1024  Batches: 1  Memory Usage: 12kB
                                      Buffers: shared hit=6
                                      ->  Seq Scan on dojo_test v0  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=3)
                                            Buffers: shared hit=6
Planning:
  Buffers: shared hit=14
Planning Time: 0.537 ms
Execution Time: 24.115 ms
{"case": "array", "product": 2, "severity": false, "count": 633794, "count_ms": 21.11738200619584}
Aggregate  (cost=9846.04..9846.05 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=13333
  InitPlan 1
    ->  Hash Join  (cost=4.75..132.94 rows=96 width=4) (actual rows=8.00 loops=1)
          Hash Cond: (v1.id = v0.engagement_id)
          Buffers: shared hit=177
          ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=1)
                Buffers: shared hit=175
                ->  Seq Scan on dojo_engagement v1  (cost=0.00..10.10 rows=10 width=8) (actual rows=24.00 loops=1)
                      Buffers: shared hit=1
                ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=24)
                      Filter: ((u1.dojo_user_id = 2) OR (u4.dojo_user_id = 2))
                      Rows Removed by Filter: 2
                      Buffers: shared hit=174
                      ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=24)
                            Buffers: shared hit=144
                            ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=24)
                                  Buffers: shared hit=96
                                  ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=24)
                                        Index Cond: (id = v1.product_id)
                                        Index Searches: 24
                                        Buffers: shared hit=48
                                  ->  Index Only Scan using dojo_product_type_pkey on dojo_product_type u3  (cost=0.14..0.96 rows=1 width=4) (actual rows=1.00 loops=24)
                                        Index Cond: (id = u0.prod_type_id)
                                        Heap Fetches: 24
                                        Index Searches: 24
                                        Buffers: shared hit=48
                            ->  Index Scan using dojo_product_type_authorized_users_product_type_id_dba7ff5f on dojo_product_type_authorized_users u4  (cost=0.15..0.96 rows=10 width=8) (actual rows=0.00 loops=24)
                                  Index Cond: (product_type_id = u3.id)
                                  Index Searches: 24
                                  Buffers: shared hit=48
                      ->  Index Scan using dojo_product_authorized_users_product_id_ffcb106e on dojo_product_authorized_users u1  (cost=0.15..1.13 rows=10 width=8) (actual rows=1.42 loops=24)
                            Index Cond: (product_id = u0.id)
                            Index Searches: 24
                            Buffers: shared hit=30
          ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                Buckets: 1024  Batches: 1  Memory Usage: 12kB
                Buffers: shared hit=2
                ->  Seq Scan on dojo_test v0  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                      Buffers: shared hit=2
  ->  Index Only Scan using dojo_finding_test_id_ef8ec5fc on dojo_finding  (cost=0.42..9464.70 rows=99361 width=0) (actual rows=633794.00 loops=1)
        Index Cond: (test_id = ANY ((InitPlan 1).col1))
        Heap Fetches: 16538
        Index Searches: 1
        Buffers: shared hit=13333
Planning:
  Buffers: shared hit=10
Planning Time: 0.376 ms
Execution Time: 22.396 ms
{"case": "baseline", "product": 2, "severity": true, "count": 63688, "count_ms": 367.0568390007247}
Aggregate  (cost=39887.69..39887.70 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=8 read=162752
  ->  Nested Loop  (cost=1193.83..39862.10 rows=10237 width=0) (actual rows=63688.00 loops=1)
        Buffers: shared hit=8 read=162752
        ->  Nested Loop Semi Join  (cost=12.83..49.10 rows=10 width=4) (actual rows=8.00 loops=1)
              Buffers: shared hit=8 read=4
              ->  Hash Join  (cost=8.16..11.42 rows=10 width=8) (actual rows=8.00 loops=1)
                    Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
                    Buffers: shared hit=2 read=2
                    ->  Seq Scan on dojo_test  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                          Buffers: shared hit=2
                    ->  Hash  (cost=8.15..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                          Buckets: 1024  Batches: 1  Memory Usage: 9kB
                          Buffers: shared read=2
                          ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                                Index Cond: (product_id = 2)
                                Index Searches: 1
                                Buffers: shared read=2
              ->  Materialize  (cost=4.67..37.50 rows=3 width=4) (actual rows=1.00 loops=8)
                    Storage: Memory  Maximum Storage: 17kB
                    Buffers: shared hit=6 read=2
                    ->  Nested Loop Left Join  (cost=4.67..37.48 rows=3 width=4) (actual rows=1.00 loops=1)
                          Filter: ((u1.dojo_user_id = 2) OR (u4.dojo_user_id = 2))
                          Buffers: shared hit=6 read=2
                          ->  Nested Loop Left Join  (cost=0.44..17.60 rows=29 width=8) (actual rows=1.00 loops=1)
                                Buffers: shared hit=5 read=1
                                ->  Nested Loop  (cost=0.28..16.54 rows=1 width=8) (actual rows=1.00 loops=1)
                                      Buffers: shared hit=3 read=1
                                      ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..8.16 rows=1 width=8) (actual rows=1.00 loops=1)
                                            Index Cond: (id = 2)
                                            Index Searches: 1
                                            Buffers: shared hit=1 read=1
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
                                Buffers: shared hit=1 read=1
                                ->  Bitmap Heap Scan on dojo_product_authorized_users u1  (cost=4.23..14.79 rows=10 width=8) (actual rows=1.00 loops=1)
                                      Recheck Cond: (product_id = 2)
                                      Heap Blocks: exact=1
                                      Buffers: shared hit=1 read=1
                                      ->  Bitmap Index Scan on dojo_product_authorized_users_product_id_ffcb106e  (cost=0.00..4.23 rows=10 width=0) (actual rows=8.00 loops=1)
                                            Index Cond: (product_id = 2)
                                            Index Searches: 1
                                            Buffers: shared read=1
        ->  Bitmap Heap Scan on dojo_finding  (cost=1181.00..3971.06 rows=1024 width=4) (actual rows=7961.00 loops=8)
              Recheck Cond: ((dojo_test.id = test_id) AND ((severity)::text = 'High'::text) AND active)
              Rows Removed by Index Recheck: 17489
              Heap Blocks: exact=161586
              Buffers: shared read=162748
              ->  BitmapAnd  (cost=1181.00..1181.00 rows=1024 width=0) (actual rows=0.00 loops=8)
                    Buffers: shared read=1162
                    ->  Bitmap Index Scan on dojo_finding_test_id_ef8ec5fc  (cost=0.00..102.47 rows=10411 width=0) (actual rows=79224.25 loops=8)
                          Index Cond: (test_id = dojo_test.id)
                          Index Searches: 8
                          Buffers: shared read=514
                    ->  Bitmap Index Scan on idx_finding_sev_active  (cost=0.00..1053.46 rows=98271 width=0) (actual rows=100225.00 loops=8)
                          Index Cond: ((severity)::text = 'High'::text)
                          Index Searches: 8
                          Buffers: shared read=648
Planning:
  Buffers: shared hit=3 read=11
Planning Time: 0.483 ms
Execution Time: 335.260 ms
{"case": "subquery", "product": 2, "severity": true, "count": 63688, "count_ms": 344.4297890018788}
Aggregate  (cost=39887.81..39887.82 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=8 read=162752
  ->  Nested Loop  (cost=1230.13..39862.22 rows=10237 width=0) (actual rows=63688.00 loops=1)
        Buffers: shared hit=8 read=162752
        ->  HashAggregate  (cost=49.13..49.23 rows=10 width=4) (actual rows=8.00 loops=1)
              Group Key: v0.id
              Batches: 1  Memory Usage: 32kB
              Buffers: shared hit=8 read=4
              ->  Nested Loop Semi Join  (cost=12.83..49.10 rows=10 width=4) (actual rows=8.00 loops=1)
                    Buffers: shared hit=8 read=4
                    ->  Hash Join  (cost=8.16..11.42 rows=10 width=8) (actual rows=8.00 loops=1)
                          Hash Cond: (v0.engagement_id = v1.id)
                          Buffers: shared hit=2 read=2
                          ->  Seq Scan on dojo_test v0  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                                Buffers: shared hit=2
                          ->  Hash  (cost=8.15..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                                Buckets: 1024  Batches: 1  Memory Usage: 9kB
                                Buffers: shared read=2
                                ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement v1  (cost=0.14..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                                      Index Cond: (product_id = 2)
                                      Index Searches: 1
                                      Buffers: shared read=2
                    ->  Materialize  (cost=4.67..37.50 rows=3 width=4) (actual rows=1.00 loops=8)
                          Storage: Memory  Maximum Storage: 17kB
                          Buffers: shared hit=6 read=2
                          ->  Nested Loop Left Join  (cost=4.67..37.48 rows=3 width=4) (actual rows=1.00 loops=1)
                                Filter: ((u1.dojo_user_id = 2) OR (u4.dojo_user_id = 2))
                                Buffers: shared hit=6 read=2
                                ->  Nested Loop Left Join  (cost=0.44..17.60 rows=29 width=8) (actual rows=1.00 loops=1)
                                      Buffers: shared hit=5 read=1
                                      ->  Nested Loop  (cost=0.28..16.54 rows=1 width=8) (actual rows=1.00 loops=1)
                                            Buffers: shared hit=3 read=1
                                            ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..8.16 rows=1 width=8) (actual rows=1.00 loops=1)
                                                  Index Cond: (id = 2)
                                                  Index Searches: 1
                                                  Buffers: shared hit=1 read=1
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
                                      Buffers: shared hit=1 read=1
                                      ->  Bitmap Heap Scan on dojo_product_authorized_users u1  (cost=4.23..14.79 rows=10 width=8) (actual rows=1.00 loops=1)
                                            Recheck Cond: (product_id = 2)
                                            Heap Blocks: exact=1
                                            Buffers: shared hit=1 read=1
                                            ->  Bitmap Index Scan on dojo_product_authorized_users_product_id_ffcb106e  (cost=0.00..4.23 rows=10 width=0) (actual rows=8.00 loops=1)
                                                  Index Cond: (product_id = 2)
                                                  Index Searches: 1
                                                  Buffers: shared read=1
        ->  Bitmap Heap Scan on dojo_finding  (cost=1181.00..3971.06 rows=1024 width=4) (actual rows=7961.00 loops=8)
              Recheck Cond: ((v0.id = test_id) AND ((severity)::text = 'High'::text) AND active)
              Rows Removed by Index Recheck: 17489
              Heap Blocks: exact=161586
              Buffers: shared read=162748
              ->  BitmapAnd  (cost=1181.00..1181.00 rows=1024 width=0) (actual rows=0.00 loops=8)
                    Buffers: shared read=1162
                    ->  Bitmap Index Scan on dojo_finding_test_id_ef8ec5fc  (cost=0.00..102.47 rows=10411 width=0) (actual rows=79224.25 loops=8)
                          Index Cond: (test_id = v0.id)
                          Index Searches: 8
                          Buffers: shared read=514
                    ->  Bitmap Index Scan on idx_finding_sev_active  (cost=0.00..1053.46 rows=98271 width=0) (actual rows=100225.00 loops=8)
                          Index Cond: ((severity)::text = 'High'::text)
                          Index Searches: 8
                          Buffers: shared read=648
Planning:
  Buffers: shared hit=1 read=13
Planning Time: 0.455 ms
Execution Time: 322.803 ms
{"case": "array", "product": 2, "severity": true, "count": 63688, "count_ms": 140.51975899928948}
Aggregate  (cost=32353.61..32353.62 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=6 read=66256
  InitPlan 1
    ->  Nested Loop Semi Join  (cost=12.83..49.10 rows=10 width=4) (actual rows=8.00 loops=1)
          Buffers: shared hit=6 read=6
          ->  Hash Join  (cost=8.16..11.42 rows=10 width=8) (actual rows=8.00 loops=1)
                Hash Cond: (v0.engagement_id = v1.id)
                Buffers: shared read=4
                ->  Seq Scan on dojo_test v0  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                      Buffers: shared read=2
                ->  Hash  (cost=8.15..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                      Buckets: 1024  Batches: 1  Memory Usage: 9kB
                      Buffers: shared read=2
                      ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement v1  (cost=0.14..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                            Index Cond: (product_id = 2)
                            Index Searches: 1
                            Buffers: shared read=2
          ->  Materialize  (cost=4.67..37.50 rows=3 width=4) (actual rows=1.00 loops=8)
                Storage: Memory  Maximum Storage: 17kB
                Buffers: shared hit=6 read=2
                ->  Nested Loop Left Join  (cost=4.67..37.48 rows=3 width=4) (actual rows=1.00 loops=1)
                      Filter: ((u1.dojo_user_id = 2) OR (u4.dojo_user_id = 2))
                      Buffers: shared hit=6 read=2
                      ->  Nested Loop Left Join  (cost=0.44..17.60 rows=29 width=8) (actual rows=1.00 loops=1)
                            Buffers: shared hit=5 read=1
                            ->  Nested Loop  (cost=0.28..16.54 rows=1 width=8) (actual rows=1.00 loops=1)
                                  Buffers: shared hit=3 read=1
                                  ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..8.16 rows=1 width=8) (actual rows=1.00 loops=1)
                                        Index Cond: (id = 2)
                                        Index Searches: 1
                                        Buffers: shared hit=1 read=1
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
                            Buffers: shared hit=1 read=1
                            ->  Bitmap Heap Scan on dojo_product_authorized_users u1  (cost=4.23..14.79 rows=10 width=8) (actual rows=1.00 loops=1)
                                  Recheck Cond: (product_id = 2)
                                  Heap Blocks: exact=1
                                  Buffers: shared hit=1 read=1
                                  ->  Bitmap Index Scan on dojo_product_authorized_users_product_id_ffcb106e  (cost=0.00..4.23 rows=10 width=0) (actual rows=8.00 loops=1)
                                        Index Cond: (product_id = 2)
                                        Index Searches: 1
                                        Buffers: shared read=1
  ->  Bitmap Heap Scan on dojo_finding  (cost=2152.04..32280.08 rows=9770 width=0) (actual rows=63688.00 loops=1)
        Recheck Cond: (((severity)::text = 'High'::text) AND active AND (test_id = ANY ((InitPlan 1).col1)))
        Rows Removed by Index Recheck: 247203
        Heap Blocks: exact=32468 lossy=33201
        Buffers: shared hit=6 read=66256
        ->  BitmapAnd  (cost=2152.04..2152.04 rows=9770 width=0) (actual rows=0.00 loops=1)
              Buffers: shared hit=6 read=587
              ->  Bitmap Index Scan on idx_finding_sev_active  (cost=0.00..1053.46 rows=98271 width=0) (actual rows=100225.00 loops=1)
                    Index Cond: ((severity)::text = 'High'::text)
                    Index Searches: 1
                    Buffers: shared read=81
              ->  Bitmap Index Scan on dojo_finding_test_id_ef8ec5fc  (cost=0.00..1093.45 rows=99361 width=0) (actual rows=633794.00 loops=1)
                    Index Cond: (test_id = ANY ((InitPlan 1).col1))
                    Index Searches: 1
                    Buffers: shared hit=6 read=506
Planning:
  Buffers: shared read=10
Planning Time: 0.380 ms
Execution Time: 125.299 ms
{"case": "auth_array_only", "product": 2, "severity": true, "count": 63688, "count_ms": 313.57390400080476}
Aggregate  (cost=15026.46..15026.47 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=175 read=162754
  InitPlan 1
    ->  Hash Join  (cost=4.75..132.94 rows=96 width=4) (actual rows=8.00 loops=1)
          Hash Cond: (v1.id = v0.engagement_id)
          Buffers: shared hit=173 read=4
          ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=1)
                Buffers: shared hit=171 read=4
                ->  Seq Scan on dojo_engagement v1  (cost=0.00..10.10 rows=10 width=8) (actual rows=24.00 loops=1)
                      Buffers: shared hit=1
                ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=24)
                      Filter: ((u1.dojo_user_id = 2) OR (u4.dojo_user_id = 2))
                      Rows Removed by Filter: 2
                      Buffers: shared hit=170 read=4
                      ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=24)
                            Buffers: shared hit=142 read=2
                            ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=24)
                                  Buffers: shared hit=94 read=2
                                  ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=24)
                                        Index Cond: (id = v1.product_id)
                                        Index Searches: 24
                                        Buffers: shared hit=46 read=2
                                  ->  Index Only Scan using dojo_product_type_pkey on dojo_product_type u3  (cost=0.14..0.96 rows=1 width=4) (actual rows=1.00 loops=24)
                                        Index Cond: (id = u0.prod_type_id)
                                        Heap Fetches: 24
                                        Index Searches: 24
                                        Buffers: shared hit=48
                            ->  Index Scan using dojo_product_type_authorized_users_product_type_id_dba7ff5f on dojo_product_type_authorized_users u4  (cost=0.15..0.96 rows=10 width=8) (actual rows=0.00 loops=24)
                                  Index Cond: (product_type_id = u3.id)
                                  Index Searches: 24
                                  Buffers: shared hit=48
                      ->  Index Scan using dojo_product_authorized_users_product_id_ffcb106e on dojo_product_authorized_users u1  (cost=0.15..1.13 rows=10 width=8) (actual rows=1.42 loops=24)
                            Index Cond: (product_id = u0.id)
                            Index Searches: 24
                            Buffers: shared hit=28 read=2
          ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                Buckets: 1024  Batches: 1  Memory Usage: 12kB
                Buffers: shared hit=2
                ->  Seq Scan on dojo_test v0  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                      Buffers: shared hit=2
  ->  Nested Loop  (cost=1104.66..14891.07 rows=977 width=0) (actual rows=63688.00 loops=1)
        Buffers: shared hit=175 read=162754
        ->  Hash Join  (cost=8.16..11.42 rows=10 width=4) (actual rows=8.00 loops=1)
              Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
              Buffers: shared hit=2 read=2
              ->  Seq Scan on dojo_test  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                    Buffers: shared hit=2
              ->  Hash  (cost=8.15..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 9kB
                    Buffers: shared read=2
                    ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                          Index Cond: (product_id = 2)
                          Index Searches: 1
                          Buffers: shared read=2
        ->  Bitmap Heap Scan on dojo_finding  (cost=1096.49..1486.95 rows=102 width=4) (actual rows=7961.00 loops=8)
              Recheck Cond: ((dojo_test.id = test_id) AND (test_id = ANY ((InitPlan 1).col1)) AND ((severity)::text = 'High'::text) AND active)
              Rows Removed by Index Recheck: 17489
              Heap Blocks: exact=161586
              Buffers: shared hit=173 read=162752
              ->  BitmapAnd  (cost=1096.49..1096.49 rows=102 width=0) (actual rows=0.00 loops=8)
                    Buffers: shared hit=173 read=1166
                    ->  Bitmap Index Scan on dojo_finding_test_id_ef8ec5fc  (cost=0.00..40.32 rows=1035 width=0) (actual rows=79224.25 loops=8)
                          Index Cond: ((test_id = dojo_test.id) AND (test_id = ANY ((InitPlan 1).col1)))
                          Index Searches: 8
                          Buffers: shared read=514
                    ->  Bitmap Index Scan on idx_finding_sev_active  (cost=0.00..1053.46 rows=98271 width=0) (actual rows=100225.00 loops=8)
                          Index Cond: ((severity)::text = 'High'::text)
                          Index Searches: 8
                          Buffers: shared read=648
Planning:
  Buffers: shared hit=5 read=11
Planning Time: 0.465 ms
Execution Time: 291.938 ms
{"case": "product_array_only", "product": 2, "severity": true, "count": 63688, "count_ms": 146.51934399444144}
Aggregate  (cost=32552.65..32552.66 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=175 read=66256
  InitPlan 1
    ->  Hash Join  (cost=8.16..11.42 rows=10 width=4) (actual rows=8.00 loops=1)
          Hash Cond: (u0_1.engagement_id = u1_1.id)
          Buffers: shared hit=3 read=1
          ->  Seq Scan on dojo_test u0_1  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                Buffers: shared hit=2
          ->  Hash  (cost=8.15..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                Buckets: 1024  Batches: 1  Memory Usage: 9kB
                Buffers: shared hit=1 read=1
                ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement u1_1  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                      Index Cond: (product_id = 2)
                      Index Searches: 1
                      Buffers: shared hit=1 read=1
  ->  Hash Join  (cost=2284.63..32516.80 rows=9770 width=0) (actual rows=63688.00 loops=1)
        Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
        Buffers: shared hit=175 read=66256
        ->  Hash Join  (cost=2156.20..32311.02 rows=9770 width=4) (actual rows=63688.00 loops=1)
              Hash Cond: (dojo_finding.test_id = dojo_test.id)
              Buffers: shared hit=5 read=66251
              ->  Bitmap Heap Scan on dojo_finding  (cost=2152.04..32280.08 rows=9770 width=4) (actual rows=63688.00 loops=1)
                    Recheck Cond: (((severity)::text = 'High'::text) AND active AND (test_id = ANY ((InitPlan 1).col1)))
                    Rows Removed by Index Recheck: 247203
                    Heap Blocks: exact=32468 lossy=33201
                    Buffers: shared hit=3 read=66251
                    ->  BitmapAnd  (cost=2152.04..2152.04 rows=9770 width=0) (actual rows=0.00 loops=1)
                          Buffers: shared hit=3 read=582
                          ->  Bitmap Index Scan on idx_finding_sev_active  (cost=0.00..1053.46 rows=98271 width=0) (actual rows=100225.00 loops=1)
                                Index Cond: ((severity)::text = 'High'::text)
                                Index Searches: 1
                                Buffers: shared read=81
                          ->  Bitmap Index Scan on dojo_finding_test_id_ef8ec5fc  (cost=0.00..1093.45 rows=99361 width=0) (actual rows=633794.00 loops=1)
                                Index Cond: (test_id = ANY ((InitPlan 1).col1))
                                Index Searches: 1
                                Buffers: shared hit=3 read=501
              ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 12kB
                    Buffers: shared hit=2
                    ->  Seq Scan on dojo_test  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                          Buffers: shared hit=2
        ->  Hash  (cost=128.30..128.30 rows=10 width=4) (actual rows=2.00 loops=1)
              Buckets: 1024  Batches: 1  Memory Usage: 9kB
              Buffers: shared hit=170 read=5
              ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=1)
                    Buffers: shared hit=170 read=5
                    ->  Seq Scan on dojo_engagement  (cost=0.00..10.10 rows=10 width=8) (actual rows=24.00 loops=1)
                          Buffers: shared read=1
                    ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=24)
                          Filter: ((u1.dojo_user_id = 2) OR (u4.dojo_user_id = 2))
                          Rows Removed by Filter: 2
                          Buffers: shared hit=170 read=4
                          ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=24)
                                Buffers: shared hit=142 read=2
                                ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=24)
                                      Buffers: shared hit=94 read=2
                                      ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=24)
                                            Index Cond: (id = dojo_engagement.product_id)
                                            Index Searches: 24
                                            Buffers: shared hit=46 read=2
                                      ->  Index Only Scan using dojo_product_type_pkey on dojo_product_type u3  (cost=0.14..0.96 rows=1 width=4) (actual rows=1.00 loops=24)
                                            Index Cond: (id = u0.prod_type_id)
                                            Heap Fetches: 24
                                            Index Searches: 24
                                            Buffers: shared hit=48
                                ->  Index Scan using dojo_product_type_authorized_users_product_type_id_dba7ff5f on dojo_product_type_authorized_users u4  (cost=0.15..0.96 rows=10 width=8) (actual rows=0.00 loops=24)
                                      Index Cond: (product_type_id = u3.id)
                                      Index Searches: 24
                                      Buffers: shared hit=48
                          ->  Index Scan using dojo_product_authorized_users_product_id_ffcb106e on dojo_product_authorized_users u1  (cost=0.15..1.13 rows=10 width=8) (actual rows=1.42 loops=24)
                                Index Cond: (product_id = u0.id)
                                Index Searches: 24
                                Buffers: shared hit=28 read=2
Planning:
  Buffers: shared hit=3 read=13
Planning Time: 0.495 ms
Execution Time: 130.463 ms
{"case": "two_arrays", "product": 2, "severity": true, "count": 63688, "count_ms": 157.76968099817168}
Aggregate  (cost=5375.54..5375.55 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=173 read=66258
  InitPlan 1
    ->  Hash Join  (cost=8.16..11.42 rows=10 width=4) (actual rows=8.00 loops=1)
          Hash Cond: (u0.engagement_id = u1.id)
          Buffers: shared read=4
          ->  Seq Scan on dojo_test u0  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                Buffers: shared read=2
          ->  Hash  (cost=8.15..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                Buckets: 1024  Batches: 1  Memory Usage: 9kB
                Buffers: shared read=2
                ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement u1  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                      Index Cond: (product_id = 2)
                      Index Searches: 1
                      Buffers: shared read=2
  InitPlan 2
    ->  Hash Join  (cost=4.75..132.94 rows=96 width=4) (actual rows=8.00 loops=1)
          Hash Cond: (v1.id = v0.engagement_id)
          Buffers: shared hit=173 read=4
          ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=1)
                Buffers: shared hit=171 read=4
                ->  Seq Scan on dojo_engagement v1  (cost=0.00..10.10 rows=10 width=8) (actual rows=24.00 loops=1)
                      Buffers: shared hit=1
                ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=24)
                      Filter: ((u1_1.dojo_user_id = 2) OR (u4.dojo_user_id = 2))
                      Rows Removed by Filter: 2
                      Buffers: shared hit=170 read=4
                      ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=24)
                            Buffers: shared hit=142 read=2
                            ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=24)
                                  Buffers: shared hit=94 read=2
                                  ->  Index Scan using dojo_product_pkey on dojo_product u0_1  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=24)
                                        Index Cond: (id = v1.product_id)
                                        Index Searches: 24
                                        Buffers: shared hit=46 read=2
                                  ->  Index Only Scan using dojo_product_type_pkey on dojo_product_type u3  (cost=0.14..0.96 rows=1 width=4) (actual rows=1.00 loops=24)
                                        Index Cond: (id = u0_1.prod_type_id)
                                        Heap Fetches: 24
                                        Index Searches: 24
                                        Buffers: shared hit=48
                            ->  Index Scan using dojo_product_type_authorized_users_product_type_id_dba7ff5f on dojo_product_type_authorized_users u4  (cost=0.15..0.96 rows=10 width=8) (actual rows=0.00 loops=24)
                                  Index Cond: (product_type_id = u3.id)
                                  Index Searches: 24
                                  Buffers: shared hit=48
                      ->  Index Scan using dojo_product_authorized_users_product_id_ffcb106e on dojo_product_authorized_users u1_1  (cost=0.15..1.13 rows=10 width=8) (actual rows=1.42 loops=24)
                            Index Cond: (product_id = u0_1.id)
                            Index Searches: 24
                            Buffers: shared hit=28 read=2
          ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                Buckets: 1024  Batches: 1  Memory Usage: 12kB
                Buffers: shared hit=2
                ->  Seq Scan on dojo_test v0  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                      Buffers: shared hit=2
  ->  Bitmap Heap Scan on dojo_finding  (cost=1575.69..5228.75 rows=971 width=0) (actual rows=63688.00 loops=1)
        Recheck Cond: ((test_id = ANY ((InitPlan 1).col1)) AND (test_id = ANY ((InitPlan 2).col1)) AND ((severity)::text = 'High'::text) AND active)
        Rows Removed by Index Recheck: 332650
        Heap Blocks: exact=27761 lossy=37908
        Buffers: shared hit=173 read=66258
        ->  BitmapAnd  (cost=1575.69..1575.69 rows=971 width=0) (actual rows=0.00 loops=1)
              Buffers: shared hit=173 read=589
              ->  Bitmap Index Scan on dojo_finding_test_id_ef8ec5fc  (cost=0.00..521.50 rows=9878 width=0) (actual rows=633794.00 loops=1)
                    Index Cond: ((test_id = ANY ((InitPlan 1).col1)) AND (test_id = ANY ((InitPlan 2).col1)))
                    Index Searches: 1
                    Buffers: shared hit=173 read=508
              ->  Bitmap Index Scan on idx_finding_sev_active  (cost=0.00..1053.46 rows=98271 width=0) (actual rows=100225.00 loops=1)
                    Index Cond: ((severity)::text = 'High'::text)
                    Index Searches: 1
                    Buffers: shared read=81
Planning:
  Buffers: shared hit=2 read=10
Planning Time: 0.435 ms
Execution Time: 165.180 ms
{"case": "orm_auth_plus_product_array", "product": 2, "severity": true, "count": 63688, "count_ms": 136.46579899796052}
Aggregate  (cost=32584.41..32584.42 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=175 read=66256
  InitPlan 1
    ->  Hash Join  (cost=8.16..11.42 rows=10 width=4) (actual rows=8.00 loops=1)
          Hash Cond: (u0_1.engagement_id = u1_1.id)
          Buffers: shared hit=3 read=1
          ->  Seq Scan on dojo_test u0_1  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                Buffers: shared hit=2
          ->  Hash  (cost=8.15..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                Buckets: 1024  Batches: 1  Memory Usage: 9kB
                Buffers: shared hit=1 read=1
                ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement u1_1  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                      Index Cond: (product_id = 2)
                      Index Searches: 1
                      Buffers: shared hit=1 read=1
  ->  Hash Semi Join  (cost=2286.18..32548.56 rows=9770 width=0) (actual rows=63688.00 loops=1)
        Hash Cond: (dojo_finding.test_id = v0.id)
        Buffers: shared hit=175 read=66256
        ->  Bitmap Heap Scan on dojo_finding  (cost=2152.04..32280.08 rows=9770 width=4) (actual rows=63688.00 loops=1)
              Recheck Cond: (((severity)::text = 'High'::text) AND active AND (test_id = ANY ((InitPlan 1).col1)))
              Rows Removed by Index Recheck: 247203
              Heap Blocks: exact=32468 lossy=33201
              Buffers: shared hit=3 read=66251
              ->  BitmapAnd  (cost=2152.04..2152.04 rows=9770 width=0) (actual rows=0.00 loops=1)
                    Buffers: shared hit=3 read=582
                    ->  Bitmap Index Scan on idx_finding_sev_active  (cost=0.00..1053.46 rows=98271 width=0) (actual rows=100225.00 loops=1)
                          Index Cond: ((severity)::text = 'High'::text)
                          Index Searches: 1
                          Buffers: shared read=81
                    ->  Bitmap Index Scan on dojo_finding_test_id_ef8ec5fc  (cost=0.00..1093.45 rows=99361 width=0) (actual rows=633794.00 loops=1)
                          Index Cond: (test_id = ANY ((InitPlan 1).col1))
                          Index Searches: 1
                          Buffers: shared hit=3 read=501
        ->  Hash  (cost=132.94..132.94 rows=96 width=4) (actual rows=8.00 loops=1)
              Buckets: 1024  Batches: 1  Memory Usage: 9kB
              Buffers: shared hit=172 read=5
              ->  Hash Join  (cost=4.75..132.94 rows=96 width=4) (actual rows=8.00 loops=1)
                    Hash Cond: (v1.id = v0.engagement_id)
                    Buffers: shared hit=172 read=5
                    ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=1)
                          Buffers: shared hit=170 read=5
                          ->  Seq Scan on dojo_engagement v1  (cost=0.00..10.10 rows=10 width=8) (actual rows=24.00 loops=1)
                                Buffers: shared read=1
                          ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=24)
                                Filter: ((u1.dojo_user_id = 2) OR (u4.dojo_user_id = 2))
                                Rows Removed by Filter: 2
                                Buffers: shared hit=170 read=4
                                ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=24)
                                      Buffers: shared hit=142 read=2
                                      ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=24)
                                            Buffers: shared hit=94 read=2
                                            ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=24)
                                                  Index Cond: (id = v1.product_id)
                                                  Index Searches: 24
                                                  Buffers: shared hit=46 read=2
                                            ->  Index Only Scan using dojo_product_type_pkey on dojo_product_type u3  (cost=0.14..0.96 rows=1 width=4) (actual rows=1.00 loops=24)
                                                  Index Cond: (id = u0.prod_type_id)
                                                  Heap Fetches: 24
                                                  Index Searches: 24
                                                  Buffers: shared hit=48
                                      ->  Index Scan using dojo_product_type_authorized_users_product_type_id_dba7ff5f on dojo_product_type_authorized_users u4  (cost=0.15..0.96 rows=10 width=8) (actual rows=0.00 loops=24)
                                            Index Cond: (product_type_id = u3.id)
                                            Index Searches: 24
                                            Buffers: shared hit=48
                                ->  Index Scan using dojo_product_authorized_users_product_id_ffcb106e on dojo_product_authorized_users u1  (cost=0.15..1.13 rows=10 width=8) (actual rows=1.42 loops=24)
                                      Index Cond: (product_id = u0.id)
                                      Index Searches: 24
                                      Buffers: shared hit=28 read=2
                    ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                          Buckets: 1024  Batches: 1  Memory Usage: 12kB
                          Buffers: shared hit=2
                          ->  Seq Scan on dojo_test v0  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                                Buffers: shared hit=2
Planning:
  Buffers: shared hit=3 read=13
Planning Time: 0.497 ms
Execution Time: 129.779 ms
{"case": "baseline", "product": 8, "severity": false, "count": 33684, "count_ms": 28.309384993917774}
Finalize Aggregate  (cost=32196.05..32196.06 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=24145
  ->  Gather  (cost=32195.83..32196.04 rows=2 width=8) (actual rows=3.00 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=24145
        ->  Partial Aggregate  (cost=31195.83..31195.84 rows=1 width=8) (actual rows=1.00 loops=3)
              Buffers: shared hit=24145
              ->  Hash Join  (cost=133.01..30154.75 rows=416432 width=0) (actual rows=11228.00 loops=3)
                    Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
                    Buffers: shared hit=24145
                    ->  Hash Join  (cost=4.58..26729.57 rows=416432 width=4) (actual rows=333333.33 loops=3)
                          Hash Cond: (dojo_finding.test_id = dojo_test.id)
                          Buffers: shared hit=23614
                          ->  Parallel Index Only Scan using dojo_finding_test_id_ef8ec5fc on dojo_finding  (cost=0.42..25584.02 rows=416432 width=4) (actual rows=333333.33 loops=3)
                                Heap Fetches: 26055
                                Index Searches: 1
                                Buffers: shared hit=23566
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
Planning Time: 0.398 ms
Execution Time: 32.257 ms
{"case": "subquery", "product": 8, "severity": false, "count": 33684, "count_ms": 13.770046003628522}
Finalize Aggregate  (cost=32967.29..32967.30 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=19479
  ->  Gather  (cost=32967.08..32967.29 rows=2 width=8) (actual rows=3.00 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=19479
        ->  Partial Aggregate  (cost=31967.08..31967.09 rows=1 width=8) (actual rows=1.00 loops=3)
              Buffers: shared hit=19479
              ->  Merge Semi Join  (cost=136.52..30926.00 rows=416432 width=0) (actual rows=11228.00 loops=3)
                    Merge Cond: (dojo_finding.test_id = v0.id)
                    Buffers: shared hit=19479
                    ->  Parallel Index Only Scan using dojo_finding_test_id_ef8ec5fc on dojo_finding  (cost=0.42..25584.02 rows=416432 width=4) (actual rows=277747.33 loops=3)
                          Heap Fetches: 21757
                          Index Searches: 1
                          Buffers: shared hit=18892
                    ->  Sort  (cost=136.10..136.34 rows=96 width=4) (actual rows=8.00 loops=3)
                          Sort Key: v0.id
                          Sort Method: quicksort  Memory: 25kB
                          Buffers: shared hit=587
                          Worker 0:  Sort Method: quicksort  Memory: 25kB
                          Worker 1:  Sort Method: quicksort  Memory: 25kB
                          ->  Hash Join  (cost=4.75..132.94 rows=96 width=4) (actual rows=8.00 loops=3)
                                Hash Cond: (v1.id = v0.engagement_id)
                                Buffers: shared hit=579
                                ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=3)
                                      Buffers: shared hit=573
                                      ->  Seq Scan on dojo_engagement v1  (cost=0.00..10.10 rows=10 width=8) (actual rows=24.00 loops=3)
                                            Buffers: shared hit=45
                                      ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=72)
                                            Filter: ((u1.dojo_user_id = 3) OR (u4.dojo_user_id = 3))
                                            Rows Removed by Filter: 2
                                            Buffers: shared hit=528
                                            ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=72)
                                                  Buffers: shared hit=436
                                                  ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=72)
                                                        Buffers: shared hit=292
                                                        ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=72)
                                                              Index Cond: (id = v1.product_id)
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
                                ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=3)
                                      Buckets: 1024  Batches: 1  Memory Usage: 12kB
                                      Buffers: shared hit=6
                                      ->  Seq Scan on dojo_test v0  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=3)
                                            Buffers: shared hit=6
Planning:
  Buffers: shared hit=14
Planning Time: 0.416 ms
Execution Time: 14.848 ms
{"case": "array", "product": 8, "severity": false, "count": 33684, "count_ms": 1.6087920012068935}
Aggregate  (cost=9846.04..9846.05 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=1132
  InitPlan 1
    ->  Hash Join  (cost=4.75..132.94 rows=96 width=4) (actual rows=8.00 loops=1)
          Hash Cond: (v1.id = v0.engagement_id)
          Buffers: shared hit=177
          ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=1)
                Buffers: shared hit=175
                ->  Seq Scan on dojo_engagement v1  (cost=0.00..10.10 rows=10 width=8) (actual rows=24.00 loops=1)
                      Buffers: shared hit=1
                ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=24)
                      Filter: ((u1.dojo_user_id = 3) OR (u4.dojo_user_id = 3))
                      Rows Removed by Filter: 2
                      Buffers: shared hit=174
                      ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=24)
                            Buffers: shared hit=144
                            ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=24)
                                  Buffers: shared hit=96
                                  ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=24)
                                        Index Cond: (id = v1.product_id)
                                        Index Searches: 24
                                        Buffers: shared hit=48
                                  ->  Index Only Scan using dojo_product_type_pkey on dojo_product_type u3  (cost=0.14..0.96 rows=1 width=4) (actual rows=1.00 loops=24)
                                        Index Cond: (id = u0.prod_type_id)
                                        Heap Fetches: 24
                                        Index Searches: 24
                                        Buffers: shared hit=48
                            ->  Index Scan using dojo_product_type_authorized_users_product_type_id_dba7ff5f on dojo_product_type_authorized_users u4  (cost=0.15..0.96 rows=10 width=8) (actual rows=0.00 loops=24)
                                  Index Cond: (product_type_id = u3.id)
                                  Index Searches: 24
                                  Buffers: shared hit=48
                      ->  Index Scan using dojo_product_authorized_users_product_id_ffcb106e on dojo_product_authorized_users u1  (cost=0.15..1.13 rows=10 width=8) (actual rows=1.42 loops=24)
                            Index Cond: (product_id = u0.id)
                            Index Searches: 24
                            Buffers: shared hit=30
          ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                Buckets: 1024  Batches: 1  Memory Usage: 12kB
                Buffers: shared hit=2
                ->  Seq Scan on dojo_test v0  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                      Buffers: shared hit=2
  ->  Index Only Scan using dojo_finding_test_id_ef8ec5fc on dojo_finding  (cost=0.42..9464.70 rows=99361 width=0) (actual rows=33684.00 loops=1)
        Index Cond: (test_id = ANY ((InitPlan 1).col1))
        Heap Fetches: 899
        Index Searches: 1
        Buffers: shared hit=1132
Planning:
  Buffers: shared hit=10
Planning Time: 0.211 ms
Execution Time: 1.312 ms
{"case": "baseline", "product": 8, "severity": true, "count": 3328, "count_ms": 50.915683998027816}
Aggregate  (cost=39887.69..39887.70 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=11330
  ->  Nested Loop  (cost=1193.83..39862.10 rows=10237 width=0) (actual rows=3328.00 loops=1)
        Buffers: shared hit=11330
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
                                Index Cond: (product_id = 8)
                                Index Searches: 1
                                Buffers: shared hit=2
              ->  Materialize  (cost=4.67..37.50 rows=3 width=4) (actual rows=1.00 loops=8)
                    Storage: Memory  Maximum Storage: 17kB
                    Buffers: shared hit=8
                    ->  Nested Loop Left Join  (cost=4.67..37.48 rows=3 width=4) (actual rows=1.00 loops=1)
                          Filter: ((u1.dojo_user_id = 3) OR (u4.dojo_user_id = 3))
                          Buffers: shared hit=8
                          ->  Nested Loop Left Join  (cost=0.44..17.60 rows=29 width=8) (actual rows=1.00 loops=1)
                                Buffers: shared hit=6
                                ->  Nested Loop  (cost=0.28..16.54 rows=1 width=8) (actual rows=1.00 loops=1)
                                      Buffers: shared hit=4
                                      ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..8.16 rows=1 width=8) (actual rows=1.00 loops=1)
                                            Index Cond: (id = 8)
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
                                      Recheck Cond: (product_id = 8)
                                      Heap Blocks: exact=1
                                      Buffers: shared hit=2
                                      ->  Bitmap Index Scan on dojo_product_authorized_users_product_id_ffcb106e  (cost=0.00..4.23 rows=10 width=0) (actual rows=8.00 loops=1)
                                            Index Cond: (product_id = 8)
                                            Index Searches: 1
                                            Buffers: shared hit=1
        ->  Bitmap Heap Scan on dojo_finding  (cost=1181.00..3971.06 rows=1024 width=4) (actual rows=416.00 loops=8)
              Recheck Cond: ((dojo_test.id = test_id) AND ((severity)::text = 'High'::text) AND active)
              Rows Removed by Index Recheck: 930
              Heap Blocks: exact=10622
              Buffers: shared hit=11318
              ->  BitmapAnd  (cost=1181.00..1181.00 rows=1024 width=0) (actual rows=0.00 loops=8)
                    Buffers: shared hit=696
                    ->  Bitmap Index Scan on dojo_finding_test_id_ef8ec5fc  (cost=0.00..102.47 rows=10411 width=0) (actual rows=4210.50 loops=8)
                          Index Cond: (test_id = dojo_test.id)
                          Index Searches: 8
                          Buffers: shared hit=48
                    ->  Bitmap Index Scan on idx_finding_sev_active  (cost=0.00..1053.46 rows=98271 width=0) (actual rows=100225.00 loops=8)
                          Index Cond: ((severity)::text = 'High'::text)
                          Index Searches: 8
                          Buffers: shared hit=648
Planning:
  Buffers: shared hit=14
Planning Time: 0.366 ms
Execution Time: 48.360 ms
{"case": "subquery", "product": 8, "severity": true, "count": 3328, "count_ms": 47.39914200035855}
Aggregate  (cost=39887.81..39887.82 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=11330
  ->  Nested Loop  (cost=1230.13..39862.22 rows=10237 width=0) (actual rows=3328.00 loops=1)
        Buffers: shared hit=11330
        ->  HashAggregate  (cost=49.13..49.23 rows=10 width=4) (actual rows=8.00 loops=1)
              Group Key: v0.id
              Batches: 1  Memory Usage: 32kB
              Buffers: shared hit=12
              ->  Nested Loop Semi Join  (cost=12.83..49.10 rows=10 width=4) (actual rows=8.00 loops=1)
                    Buffers: shared hit=12
                    ->  Hash Join  (cost=8.16..11.42 rows=10 width=8) (actual rows=8.00 loops=1)
                          Hash Cond: (v0.engagement_id = v1.id)
                          Buffers: shared hit=4
                          ->  Seq Scan on dojo_test v0  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                                Buffers: shared hit=2
                          ->  Hash  (cost=8.15..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                                Buckets: 1024  Batches: 1  Memory Usage: 9kB
                                Buffers: shared hit=2
                                ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement v1  (cost=0.14..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                                      Index Cond: (product_id = 8)
                                      Index Searches: 1
                                      Buffers: shared hit=2
                    ->  Materialize  (cost=4.67..37.50 rows=3 width=4) (actual rows=1.00 loops=8)
                          Storage: Memory  Maximum Storage: 17kB
                          Buffers: shared hit=8
                          ->  Nested Loop Left Join  (cost=4.67..37.48 rows=3 width=4) (actual rows=1.00 loops=1)
                                Filter: ((u1.dojo_user_id = 3) OR (u4.dojo_user_id = 3))
                                Buffers: shared hit=8
                                ->  Nested Loop Left Join  (cost=0.44..17.60 rows=29 width=8) (actual rows=1.00 loops=1)
                                      Buffers: shared hit=6
                                      ->  Nested Loop  (cost=0.28..16.54 rows=1 width=8) (actual rows=1.00 loops=1)
                                            Buffers: shared hit=4
                                            ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..8.16 rows=1 width=8) (actual rows=1.00 loops=1)
                                                  Index Cond: (id = 8)
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
                                            Recheck Cond: (product_id = 8)
                                            Heap Blocks: exact=1
                                            Buffers: shared hit=2
                                            ->  Bitmap Index Scan on dojo_product_authorized_users_product_id_ffcb106e  (cost=0.00..4.23 rows=10 width=0) (actual rows=8.00 loops=1)
                                                  Index Cond: (product_id = 8)
                                                  Index Searches: 1
                                                  Buffers: shared hit=1
        ->  Bitmap Heap Scan on dojo_finding  (cost=1181.00..3971.06 rows=1024 width=4) (actual rows=416.00 loops=8)
              Recheck Cond: ((v0.id = test_id) AND ((severity)::text = 'High'::text) AND active)
              Rows Removed by Index Recheck: 930
              Heap Blocks: exact=10622
              Buffers: shared hit=11318
              ->  BitmapAnd  (cost=1181.00..1181.00 rows=1024 width=0) (actual rows=0.00 loops=8)
                    Buffers: shared hit=696
                    ->  Bitmap Index Scan on dojo_finding_test_id_ef8ec5fc  (cost=0.00..102.47 rows=10411 width=0) (actual rows=4210.50 loops=8)
                          Index Cond: (test_id = v0.id)
                          Index Searches: 8
                          Buffers: shared hit=48
                    ->  Bitmap Index Scan on idx_finding_sev_active  (cost=0.00..1053.46 rows=98271 width=0) (actual rows=100225.00 loops=8)
                          Index Cond: ((severity)::text = 'High'::text)
                          Index Searches: 8
                          Buffers: shared hit=648
Planning:
  Buffers: shared hit=14
Planning Time: 0.371 ms
Execution Time: 47.119 ms
{"case": "array", "product": 8, "severity": true, "count": 3328, "count_ms": 21.480923998751678}
Aggregate  (cost=32353.61..32353.62 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=9833
  InitPlan 1
    ->  Nested Loop Semi Join  (cost=12.83..49.10 rows=10 width=4) (actual rows=8.00 loops=1)
          Buffers: shared hit=12
          ->  Hash Join  (cost=8.16..11.42 rows=10 width=8) (actual rows=8.00 loops=1)
                Hash Cond: (v0.engagement_id = v1.id)
                Buffers: shared hit=4
                ->  Seq Scan on dojo_test v0  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                      Buffers: shared hit=2
                ->  Hash  (cost=8.15..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                      Buckets: 1024  Batches: 1  Memory Usage: 9kB
                      Buffers: shared hit=2
                      ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement v1  (cost=0.14..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                            Index Cond: (product_id = 8)
                            Index Searches: 1
                            Buffers: shared hit=2
          ->  Materialize  (cost=4.67..37.50 rows=3 width=4) (actual rows=1.00 loops=8)
                Storage: Memory  Maximum Storage: 17kB
                Buffers: shared hit=8
                ->  Nested Loop Left Join  (cost=4.67..37.48 rows=3 width=4) (actual rows=1.00 loops=1)
                      Filter: ((u1.dojo_user_id = 3) OR (u4.dojo_user_id = 3))
                      Buffers: shared hit=8
                      ->  Nested Loop Left Join  (cost=0.44..17.60 rows=29 width=8) (actual rows=1.00 loops=1)
                            Buffers: shared hit=6
                            ->  Nested Loop  (cost=0.28..16.54 rows=1 width=8) (actual rows=1.00 loops=1)
                                  Buffers: shared hit=4
                                  ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..8.16 rows=1 width=8) (actual rows=1.00 loops=1)
                                        Index Cond: (id = 8)
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
                                  Recheck Cond: (product_id = 8)
                                  Heap Blocks: exact=1
                                  Buffers: shared hit=2
                                  ->  Bitmap Index Scan on dojo_product_authorized_users_product_id_ffcb106e  (cost=0.00..4.23 rows=10 width=0) (actual rows=8.00 loops=1)
                                        Index Cond: (product_id = 8)
                                        Index Searches: 1
                                        Buffers: shared hit=1
  ->  Bitmap Heap Scan on dojo_finding  (cost=2152.04..32280.08 rows=9770 width=0) (actual rows=3328.00 loops=1)
        Recheck Cond: (((severity)::text = 'High'::text) AND active AND (test_id = ANY ((InitPlan 1).col1)))
        Rows Removed by Index Recheck: 63116
        Heap Blocks: exact=1749 lossy=7957
        Buffers: shared hit=9833
        ->  BitmapAnd  (cost=2152.04..2152.04 rows=9770 width=0) (actual rows=0.00 loops=1)
              Buffers: shared hit=127
              ->  Bitmap Index Scan on idx_finding_sev_active  (cost=0.00..1053.46 rows=98271 width=0) (actual rows=100225.00 loops=1)
                    Index Cond: ((severity)::text = 'High'::text)
                    Index Searches: 1
                    Buffers: shared hit=81
              ->  Bitmap Index Scan on dojo_finding_test_id_ef8ec5fc  (cost=0.00..1093.45 rows=99361 width=0) (actual rows=33684.00 loops=1)
                    Index Cond: (test_id = ANY ((InitPlan 1).col1))
                    Index Searches: 1
                    Buffers: shared hit=46
Planning:
  Buffers: shared hit=10
Planning Time: 0.296 ms
Execution Time: 20.832 ms
{"case": "auth_array_only", "product": 8, "severity": true, "count": 3328, "count_ms": 46.21130799932871}
Aggregate  (cost=15026.46..15026.47 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=11499
  InitPlan 1
    ->  Hash Join  (cost=4.75..132.94 rows=96 width=4) (actual rows=8.00 loops=1)
          Hash Cond: (v1.id = v0.engagement_id)
          Buffers: shared hit=177
          ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=1)
                Buffers: shared hit=175
                ->  Seq Scan on dojo_engagement v1  (cost=0.00..10.10 rows=10 width=8) (actual rows=24.00 loops=1)
                      Buffers: shared hit=1
                ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=24)
                      Filter: ((u1.dojo_user_id = 3) OR (u4.dojo_user_id = 3))
                      Rows Removed by Filter: 2
                      Buffers: shared hit=174
                      ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=24)
                            Buffers: shared hit=144
                            ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=24)
                                  Buffers: shared hit=96
                                  ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=24)
                                        Index Cond: (id = v1.product_id)
                                        Index Searches: 24
                                        Buffers: shared hit=48
                                  ->  Index Only Scan using dojo_product_type_pkey on dojo_product_type u3  (cost=0.14..0.96 rows=1 width=4) (actual rows=1.00 loops=24)
                                        Index Cond: (id = u0.prod_type_id)
                                        Heap Fetches: 24
                                        Index Searches: 24
                                        Buffers: shared hit=48
                            ->  Index Scan using dojo_product_type_authorized_users_product_type_id_dba7ff5f on dojo_product_type_authorized_users u4  (cost=0.15..0.96 rows=10 width=8) (actual rows=0.00 loops=24)
                                  Index Cond: (product_type_id = u3.id)
                                  Index Searches: 24
                                  Buffers: shared hit=48
                      ->  Index Scan using dojo_product_authorized_users_product_id_ffcb106e on dojo_product_authorized_users u1  (cost=0.15..1.13 rows=10 width=8) (actual rows=1.42 loops=24)
                            Index Cond: (product_id = u0.id)
                            Index Searches: 24
                            Buffers: shared hit=30
          ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                Buckets: 1024  Batches: 1  Memory Usage: 12kB
                Buffers: shared hit=2
                ->  Seq Scan on dojo_test v0  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                      Buffers: shared hit=2
  ->  Nested Loop  (cost=1104.66..14891.07 rows=977 width=0) (actual rows=3328.00 loops=1)
        Buffers: shared hit=11499
        ->  Hash Join  (cost=8.16..11.42 rows=10 width=4) (actual rows=8.00 loops=1)
              Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
              Buffers: shared hit=4
              ->  Seq Scan on dojo_test  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                    Buffers: shared hit=2
              ->  Hash  (cost=8.15..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 9kB
                    Buffers: shared hit=2
                    ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                          Index Cond: (product_id = 8)
                          Index Searches: 1
                          Buffers: shared hit=2
        ->  Bitmap Heap Scan on dojo_finding  (cost=1096.49..1486.95 rows=102 width=4) (actual rows=416.00 loops=8)
              Recheck Cond: ((dojo_test.id = test_id) AND (test_id = ANY ((InitPlan 1).col1)) AND ((severity)::text = 'High'::text) AND active)
              Rows Removed by Index Recheck: 930
              Heap Blocks: exact=10622
              Buffers: shared hit=11495
              ->  BitmapAnd  (cost=1096.49..1096.49 rows=102 width=0) (actual rows=0.00 loops=8)
                    Buffers: shared hit=873
                    ->  Bitmap Index Scan on dojo_finding_test_id_ef8ec5fc  (cost=0.00..40.32 rows=1035 width=0) (actual rows=4210.50 loops=8)
                          Index Cond: ((test_id = dojo_test.id) AND (test_id = ANY ((InitPlan 1).col1)))
                          Index Searches: 8
                          Buffers: shared hit=48
                    ->  Bitmap Index Scan on idx_finding_sev_active  (cost=0.00..1053.46 rows=98271 width=0) (actual rows=100225.00 loops=8)
                          Index Cond: ((severity)::text = 'High'::text)
                          Index Searches: 8
                          Buffers: shared hit=648
Planning:
  Buffers: shared hit=16
Planning Time: 0.432 ms
Execution Time: 45.277 ms
{"case": "product_array_only", "product": 8, "severity": true, "count": 3328, "count_ms": 20.98000700061675}
Aggregate  (cost=32552.65..32552.66 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=10002
  InitPlan 1
    ->  Hash Join  (cost=8.16..11.42 rows=10 width=4) (actual rows=8.00 loops=1)
          Hash Cond: (u0_1.engagement_id = u1_1.id)
          Buffers: shared hit=4
          ->  Seq Scan on dojo_test u0_1  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                Buffers: shared hit=2
          ->  Hash  (cost=8.15..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                Buckets: 1024  Batches: 1  Memory Usage: 9kB
                Buffers: shared hit=2
                ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement u1_1  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                      Index Cond: (product_id = 8)
                      Index Searches: 1
                      Buffers: shared hit=2
  ->  Hash Join  (cost=2284.63..32516.80 rows=9770 width=0) (actual rows=3328.00 loops=1)
        Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
        Buffers: shared hit=10002
        ->  Hash Join  (cost=2156.20..32311.02 rows=9770 width=4) (actual rows=3328.00 loops=1)
              Hash Cond: (dojo_finding.test_id = dojo_test.id)
              Buffers: shared hit=9827
              ->  Bitmap Heap Scan on dojo_finding  (cost=2152.04..32280.08 rows=9770 width=4) (actual rows=3328.00 loops=1)
                    Recheck Cond: (((severity)::text = 'High'::text) AND active AND (test_id = ANY ((InitPlan 1).col1)))
                    Rows Removed by Index Recheck: 63116
                    Heap Blocks: exact=1749 lossy=7957
                    Buffers: shared hit=9825
                    ->  BitmapAnd  (cost=2152.04..2152.04 rows=9770 width=0) (actual rows=0.00 loops=1)
                          Buffers: shared hit=119
                          ->  Bitmap Index Scan on idx_finding_sev_active  (cost=0.00..1053.46 rows=98271 width=0) (actual rows=100225.00 loops=1)
                                Index Cond: ((severity)::text = 'High'::text)
                                Index Searches: 1
                                Buffers: shared hit=81
                          ->  Bitmap Index Scan on dojo_finding_test_id_ef8ec5fc  (cost=0.00..1093.45 rows=99361 width=0) (actual rows=33684.00 loops=1)
                                Index Cond: (test_id = ANY ((InitPlan 1).col1))
                                Index Searches: 1
                                Buffers: shared hit=38
              ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 12kB
                    Buffers: shared hit=2
                    ->  Seq Scan on dojo_test  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                          Buffers: shared hit=2
        ->  Hash  (cost=128.30..128.30 rows=10 width=4) (actual rows=2.00 loops=1)
              Buckets: 1024  Batches: 1  Memory Usage: 9kB
              Buffers: shared hit=175
              ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=1)
                    Buffers: shared hit=175
                    ->  Seq Scan on dojo_engagement  (cost=0.00..10.10 rows=10 width=8) (actual rows=24.00 loops=1)
                          Buffers: shared hit=1
                    ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=24)
                          Filter: ((u1.dojo_user_id = 3) OR (u4.dojo_user_id = 3))
                          Rows Removed by Filter: 2
                          Buffers: shared hit=174
                          ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=24)
                                Buffers: shared hit=144
                                ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=24)
                                      Buffers: shared hit=96
                                      ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=24)
                                            Index Cond: (id = dojo_engagement.product_id)
                                            Index Searches: 24
                                            Buffers: shared hit=48
                                      ->  Index Only Scan using dojo_product_type_pkey on dojo_product_type u3  (cost=0.14..0.96 rows=1 width=4) (actual rows=1.00 loops=24)
                                            Index Cond: (id = u0.prod_type_id)
                                            Heap Fetches: 24
                                            Index Searches: 24
                                            Buffers: shared hit=48
                                ->  Index Scan using dojo_product_type_authorized_users_product_type_id_dba7ff5f on dojo_product_type_authorized_users u4  (cost=0.15..0.96 rows=10 width=8) (actual rows=0.00 loops=24)
                                      Index Cond: (product_type_id = u3.id)
                                      Index Searches: 24
                                      Buffers: shared hit=48
                          ->  Index Scan using dojo_product_authorized_users_product_id_ffcb106e on dojo_product_authorized_users u1  (cost=0.15..1.13 rows=10 width=8) (actual rows=1.42 loops=24)
                                Index Cond: (product_id = u0.id)
                                Index Searches: 24
                                Buffers: shared hit=30
Planning:
  Buffers: shared hit=16
Planning Time: 0.417 ms
Execution Time: 20.750 ms
{"case": "two_arrays", "product": 8, "severity": true, "count": 3328, "count_ms": 14.573795997421257}
Aggregate  (cost=5375.54..5375.55 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=10002
  InitPlan 1
    ->  Hash Join  (cost=8.16..11.42 rows=10 width=4) (actual rows=8.00 loops=1)
          Hash Cond: (u0.engagement_id = u1.id)
          Buffers: shared hit=4
          ->  Seq Scan on dojo_test u0  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                Buffers: shared hit=2
          ->  Hash  (cost=8.15..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                Buckets: 1024  Batches: 1  Memory Usage: 9kB
                Buffers: shared hit=2
                ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement u1  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                      Index Cond: (product_id = 8)
                      Index Searches: 1
                      Buffers: shared hit=2
  InitPlan 2
    ->  Hash Join  (cost=4.75..132.94 rows=96 width=4) (actual rows=8.00 loops=1)
          Hash Cond: (v1.id = v0.engagement_id)
          Buffers: shared hit=177
          ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=1)
                Buffers: shared hit=175
                ->  Seq Scan on dojo_engagement v1  (cost=0.00..10.10 rows=10 width=8) (actual rows=24.00 loops=1)
                      Buffers: shared hit=1
                ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=24)
                      Filter: ((u1_1.dojo_user_id = 3) OR (u4.dojo_user_id = 3))
                      Rows Removed by Filter: 2
                      Buffers: shared hit=174
                      ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=24)
                            Buffers: shared hit=144
                            ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=24)
                                  Buffers: shared hit=96
                                  ->  Index Scan using dojo_product_pkey on dojo_product u0_1  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=24)
                                        Index Cond: (id = v1.product_id)
                                        Index Searches: 24
                                        Buffers: shared hit=48
                                  ->  Index Only Scan using dojo_product_type_pkey on dojo_product_type u3  (cost=0.14..0.96 rows=1 width=4) (actual rows=1.00 loops=24)
                                        Index Cond: (id = u0_1.prod_type_id)
                                        Heap Fetches: 24
                                        Index Searches: 24
                                        Buffers: shared hit=48
                            ->  Index Scan using dojo_product_type_authorized_users_product_type_id_dba7ff5f on dojo_product_type_authorized_users u4  (cost=0.15..0.96 rows=10 width=8) (actual rows=0.00 loops=24)
                                  Index Cond: (product_type_id = u3.id)
                                  Index Searches: 24
                                  Buffers: shared hit=48
                      ->  Index Scan using dojo_product_authorized_users_product_id_ffcb106e on dojo_product_authorized_users u1_1  (cost=0.15..1.13 rows=10 width=8) (actual rows=1.42 loops=24)
                            Index Cond: (product_id = u0_1.id)
                            Index Searches: 24
                            Buffers: shared hit=30
          ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                Buckets: 1024  Batches: 1  Memory Usage: 12kB
                Buffers: shared hit=2
                ->  Seq Scan on dojo_test v0  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                      Buffers: shared hit=2
  ->  Bitmap Heap Scan on dojo_finding  (cost=1575.69..5228.75 rows=971 width=0) (actual rows=3328.00 loops=1)
        Recheck Cond: ((test_id = ANY ((InitPlan 1).col1)) AND (test_id = ANY ((InitPlan 2).col1)) AND ((severity)::text = 'High'::text) AND active)
        Rows Removed by Index Recheck: 7442
        Heap Blocks: exact=9706
        Buffers: shared hit=10002
        ->  BitmapAnd  (cost=1575.69..1575.69 rows=971 width=0) (actual rows=0.00 loops=1)
              Buffers: shared hit=296
              ->  Bitmap Index Scan on dojo_finding_test_id_ef8ec5fc  (cost=0.00..521.50 rows=9878 width=0) (actual rows=33684.00 loops=1)
                    Index Cond: ((test_id = ANY ((InitPlan 1).col1)) AND (test_id = ANY ((InitPlan 2).col1)))
                    Index Searches: 1
                    Buffers: shared hit=215
              ->  Bitmap Index Scan on idx_finding_sev_active  (cost=0.00..1053.46 rows=98271 width=0) (actual rows=100225.00 loops=1)
                    Index Cond: ((severity)::text = 'High'::text)
                    Index Searches: 1
                    Buffers: shared hit=81
Planning:
  Buffers: shared hit=12
Planning Time: 0.397 ms
Execution Time: 13.059 ms
{"case": "orm_auth_plus_product_array", "product": 8, "severity": true, "count": 3328, "count_ms": 22.531258000526577}
Aggregate  (cost=32584.41..32584.42 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=10002
  InitPlan 1
    ->  Hash Join  (cost=8.16..11.42 rows=10 width=4) (actual rows=8.00 loops=1)
          Hash Cond: (u0_1.engagement_id = u1_1.id)
          Buffers: shared hit=4
          ->  Seq Scan on dojo_test u0_1  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                Buffers: shared hit=2
          ->  Hash  (cost=8.15..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                Buckets: 1024  Batches: 1  Memory Usage: 9kB
                Buffers: shared hit=2
                ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement u1_1  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                      Index Cond: (product_id = 8)
                      Index Searches: 1
                      Buffers: shared hit=2
  ->  Hash Semi Join  (cost=2286.18..32548.56 rows=9770 width=0) (actual rows=3328.00 loops=1)
        Hash Cond: (dojo_finding.test_id = v0.id)
        Buffers: shared hit=10002
        ->  Bitmap Heap Scan on dojo_finding  (cost=2152.04..32280.08 rows=9770 width=4) (actual rows=3328.00 loops=1)
              Recheck Cond: (((severity)::text = 'High'::text) AND active AND (test_id = ANY ((InitPlan 1).col1)))
              Rows Removed by Index Recheck: 63116
              Heap Blocks: exact=1749 lossy=7957
              Buffers: shared hit=9825
              ->  BitmapAnd  (cost=2152.04..2152.04 rows=9770 width=0) (actual rows=0.00 loops=1)
                    Buffers: shared hit=119
                    ->  Bitmap Index Scan on idx_finding_sev_active  (cost=0.00..1053.46 rows=98271 width=0) (actual rows=100225.00 loops=1)
                          Index Cond: ((severity)::text = 'High'::text)
                          Index Searches: 1
                          Buffers: shared hit=81
                    ->  Bitmap Index Scan on dojo_finding_test_id_ef8ec5fc  (cost=0.00..1093.45 rows=99361 width=0) (actual rows=33684.00 loops=1)
                          Index Cond: (test_id = ANY ((InitPlan 1).col1))
                          Index Searches: 1
                          Buffers: shared hit=38
        ->  Hash  (cost=132.94..132.94 rows=96 width=4) (actual rows=8.00 loops=1)
              Buckets: 1024  Batches: 1  Memory Usage: 9kB
              Buffers: shared hit=177
              ->  Hash Join  (cost=4.75..132.94 rows=96 width=4) (actual rows=8.00 loops=1)
                    Hash Cond: (v1.id = v0.engagement_id)
                    Buffers: shared hit=177
                    ->  Nested Loop Semi Join  (cost=0.59..128.30 rows=10 width=4) (actual rows=2.00 loops=1)
                          Buffers: shared hit=175
                          ->  Seq Scan on dojo_engagement v1  (cost=0.00..10.10 rows=10 width=8) (actual rows=24.00 loops=1)
                                Buffers: shared hit=1
                          ->  Nested Loop Left Join  (cost=0.59..42.84 rows=10 width=4) (actual rows=0.08 loops=24)
                                Filter: ((u1.dojo_user_id = 3) OR (u4.dojo_user_id = 3))
                                Rows Removed by Filter: 2
                                Buffers: shared hit=174
                                ->  Nested Loop Left Join  (cost=0.44..5.80 rows=29 width=8) (actual rows=1.00 loops=24)
                                      Buffers: shared hit=144
                                      ->  Nested Loop  (cost=0.28..4.74 rows=1 width=8) (actual rows=1.00 loops=24)
                                            Buffers: shared hit=96
                                            ->  Index Scan using dojo_product_pkey on dojo_product u0  (cost=0.14..3.76 rows=1 width=8) (actual rows=1.00 loops=24)
                                                  Index Cond: (id = v1.product_id)
                                                  Index Searches: 24
                                                  Buffers: shared hit=48
                                            ->  Index Only Scan using dojo_product_type_pkey on dojo_product_type u3  (cost=0.14..0.96 rows=1 width=4) (actual rows=1.00 loops=24)
                                                  Index Cond: (id = u0.prod_type_id)
                                                  Heap Fetches: 24
                                                  Index Searches: 24
                                                  Buffers: shared hit=48
                                      ->  Index Scan using dojo_product_type_authorized_users_product_type_id_dba7ff5f on dojo_product_type_authorized_users u4  (cost=0.15..0.96 rows=10 width=8) (actual rows=0.00 loops=24)
                                            Index Cond: (product_type_id = u3.id)
                                            Index Searches: 24
                                            Buffers: shared hit=48
                                ->  Index Scan using dojo_product_authorized_users_product_id_ffcb106e on dojo_product_authorized_users u1  (cost=0.15..1.13 rows=10 width=8) (actual rows=1.42 loops=24)
                                      Index Cond: (product_id = u0.id)
                                      Index Searches: 24
                                      Buffers: shared hit=30
                    ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                          Buckets: 1024  Batches: 1  Memory Usage: 12kB
                          Buffers: shared hit=2
                          ->  Seq Scan on dojo_test v0  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                                Buffers: shared hit=2
Planning:
  Buffers: shared hit=16
Planning Time: 0.423 ms
Execution Time: 19.952 ms
