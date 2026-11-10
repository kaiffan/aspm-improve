141 objects imported automatically (use -v 2 for details).

## Proposed exact count for product 2
GroupAggregate  (cost=0.70..4460.11 rows=1 width=12) (actual rows=1.00 loops=1)
  Buffers: shared hit=10633 read=2293
  ->  Nested Loop  (cost=0.70..4250.77 rows=83730 width=4) (actual rows=532569.00 loops=1)
        Buffers: shared hit=10633 read=2293
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
              Buffers: shared hit=10628 read=2293
Planning:
  Buffers: shared hit=1246 read=71
Planning Time: 6.230 ms
Execution Time: 103.069 ms
## Existing IDs, isolated cardinality 10000
Aggregate  (cost=1830.86..1830.87 rows=1 width=32) (actual rows=1.00 loops=1)
  Buffers: shared hit=359 read=1543
  ->  Limit  (cost=0.42..1805.86 rows=10000 width=4) (actual rows=10000.00 loops=1)
        Buffers: shared hit=359 read=1543
        ->  Index Scan using dojo_finding_pkey on dojo_finding  (cost=0.42..151168.53 rows=837295 width=4) (actual rows=10000.00 loops=1)
              Filter: active
              Rows Removed by Filter: 1999
              Index Searches: 1
              Buffers: shared hit=359 read=1543
Planning:
  Buffers: shared hit=14
Planning Time: 0.267 ms
Execution Time: 49.726 ms
## Existing IDs, isolated cardinality 100000
Aggregate  (cost=18304.77..18304.78 rows=1 width=32) (actual rows=1.00 loops=1)
  Buffers: shared hit=5028 read=13692
  ->  Limit  (cost=0.42..18054.77 rows=100000 width=4) (actual rows=100000.00 loops=1)
        Buffers: shared hit=5028 read=13692
        ->  Index Scan using dojo_finding_pkey on dojo_finding  (cost=0.42..151168.53 rows=837295 width=4) (actual rows=100000.00 loops=1)
              Filter: active
              Rows Removed by Filter: 19159
              Index Searches: 1
              Buffers: shared hit=5028 read=13692
Planning:
  Buffers: shared hit=2
Planning Time: 0.257 ms
Execution Time: 172.216 ms
## Existing IDs, isolated cardinality 500000
Aggregate  (cost=91522.14..91522.15 rows=1 width=32) (actual rows=1.00 loops=1)
  Buffers: shared hit=21858 read=71584
  ->  Limit  (cost=0.42..90272.14 rows=500000 width=4) (actual rows=500000.00 loops=1)
        Buffers: shared hit=21858 read=71584
        ->  Index Scan using dojo_finding_pkey on dojo_finding  (cost=0.42..151168.53 rows=837295 width=4) (actual rows=500000.00 loops=1)
              Filter: active
              Rows Removed by Filter: 95285
              Index Searches: 1
              Buffers: shared hit=21858 read=71584
Planning:
  Buffers: shared hit=2
Planning Time: 0.175 ms
Execution Time: 983.733 ms
## Existing IDs, isolated cardinality 1000000
Aggregate  (cost=31732.64..31732.65 rows=1 width=32) (actual rows=1.00 loops=1)
  Buffers: shared hit=1116 read=5711
  ->  Limit  (cost=0.42..29234.05 rows=999437 width=4) (actual rows=1000000.00 loops=1)
        Buffers: shared hit=1116 read=5711
        ->  Index Only Scan using dojo_finding_pkey on dojo_finding  (cost=0.42..29234.05 rows=999437 width=4) (actual rows=1000000.00 loops=1)
              Heap Fetches: 26055
              Index Searches: 1
              Buffers: shared hit=1116 read=5711
Planning:
  Buffers: shared read=5
Planning Time: 0.495 ms
Execution Time: 154.336 ms
