141 objects imported automatically (use -v 2 for details).

{"case": "findings", "url": "/api/v2/findings/?limit=100", "status": 200, "sql_count": 24, "sql_ms": 31.971, "fetch_ms": 0, "django_ms": 206.604, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_finding / 24890b89": 1, "dojo_finding / 6f347a8b": 1, "dojo_locationfindingreference / 7232ecb7": 1, "auth_user / c717d892": 1, "dojo_test_type / 9210c588": 1, "dojo_notes / 24579f35": 1, "dojo_risk_acceptance / 40c15205": 1, "dojo_test / d61f5eb7": 1, "dojo_tagulous_finding_tags / 6e492e55": 1, "dojo_jira_issue / b01edc2a": 1, "dojo_finding_group / baac0f4d": 1, "dojo_fileupload / dc5354fd": 1, "dojo_burprawrequestresponse / 4c41c852": 1, "dojo_endpoint_status / bd0088ca": 1, "dojo_dojometa / 0ad748ba": 1, "dojo_test_type / 7a604a36": 1, "dojo_engagement / 5e7afcc8": 1, "dojo_product / 14906c2b": 1, "dojo_product_type / d8070c78": 1, "dojo_finding_cwe / 8168aedd": 1, "dojo_findingvulnerabilityreference / 787dc19d": 1}, "bytes": 283879}
### findings: dojo_finding / 24890b89, observed 22.71 ms
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
Planning Time: 0.141 ms
Execution Time: 24.343 ms
{"case": "finding_detail", "url": "/api/v2/findings/1000000/", "status": 200, "sql_count": 23, "sql_ms": 3.874, "fetch_ms": 0, "django_ms": 21.945, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_finding / 5f6449df": 1, "dojo_locationfindingreference / 6aee1d80": 1, "auth_user / 2cd8f31a": 1, "dojo_test_type / 512424f1": 1, "dojo_notes / acb7902e": 1, "dojo_risk_acceptance / 1d462d15": 1, "dojo_test / 4c011d0e": 1, "dojo_tagulous_finding_tags / 86947250": 1, "dojo_jira_issue / b1f9f5d5": 1, "dojo_finding_group / 820c377b": 1, "dojo_fileupload / 741b65b7": 1, "dojo_burprawrequestresponse / eeee3915": 1, "dojo_endpoint_status / 36daf5b7": 1, "dojo_dojometa / fd816624": 1, "dojo_test_type / 7a604a36": 1, "dojo_engagement / 925456a2": 1, "dojo_product / b10d7cde": 1, "dojo_product_type / d8070c78": 1, "dojo_finding_cwe / bbae548e": 1, "dojo_findingvulnerabilityreference / 04792eed": 1}, "bytes": 3161}
{"case": "findings_high_active", "url": "/api/v2/findings/?limit=100&severity=High&active=true", "status": 200, "sql_count": 24, "sql_ms": 15.31, "fetch_ms": 0, "django_ms": 106.971, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_finding / 543b893d": 1, "dojo_finding / aa426bce": 1, "dojo_locationfindingreference / 7232ecb7": 1, "auth_user / c717d892": 1, "dojo_test_type / 9210c588": 1, "dojo_notes / 24579f35": 1, "dojo_risk_acceptance / 40c15205": 1, "dojo_test / 5e049563": 1, "dojo_tagulous_finding_tags / 6e492e55": 1, "dojo_jira_issue / b01edc2a": 1, "dojo_finding_group / baac0f4d": 1, "dojo_fileupload / dc5354fd": 1, "dojo_burprawrequestresponse / 4c41c852": 1, "dojo_endpoint_status / bd0088ca": 1, "dojo_dojometa / 0ad748ba": 1, "dojo_test_type / 7a604a36": 1, "dojo_engagement / b6df710f": 1, "dojo_product / 14906c2b": 1, "dojo_product_type / d8070c78": 1, "dojo_finding_cwe / 8168aedd": 1, "dojo_findingvulnerabilityreference / 787dc19d": 1}, "bytes": 282342}
### findings_high_active: dojo_finding / 543b893d, observed 7.00 ms
SELECT <projection> FROM "dojo_finding" WHERE ("dojo_finding"."severity" IN (%s) AND "dojo_finding"."active")
Aggregate  (cost=9285.36..9285.37 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=1901
  ->  Index Only Scan using idx_finding_sev_active on dojo_finding  (cost=0.42..9039.68 rows=98271 width=0) (actual rows=100225.00 loops=1)
        Index Cond: (severity = '?'::text)
        Heap Fetches: 2541
        Index Searches: 1
        Buffers: shared hit=1901
Planning:
  Buffers: shared hit=2
Planning Time: 0.147 ms
Execution Time: 8.101 ms
{"case": "findings_offset_500k", "url": "/api/v2/findings/?limit=100&offset=500000", "status": 200, "sql_count": 24, "sql_ms": 372.079, "fetch_ms": 0, "django_ms": 466.5, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_finding / 24890b89": 1, "dojo_finding / 74811f68": 1, "dojo_locationfindingreference / 7232ecb7": 1, "auth_user / c717d892": 1, "dojo_test_type / 9210c588": 1, "dojo_notes / 24579f35": 1, "dojo_risk_acceptance / 40c15205": 1, "dojo_test / ee10437d": 1, "dojo_tagulous_finding_tags / 6e492e55": 1, "dojo_jira_issue / b01edc2a": 1, "dojo_finding_group / baac0f4d": 1, "dojo_fileupload / dc5354fd": 1, "dojo_burprawrequestresponse / 4c41c852": 1, "dojo_endpoint_status / bd0088ca": 1, "dojo_dojometa / 0ad748ba": 1, "dojo_test_type / 7a604a36": 1, "dojo_engagement / 601e4b24": 1, "dojo_product / 14906c2b": 1, "dojo_product_type / d8070c78": 1, "dojo_finding_cwe / 8168aedd": 1, "dojo_findingvulnerabilityreference / 787dc19d": 1}, "bytes": 287120}
### findings_offset_500k: dojo_finding / 74811f68, observed 329.19 ms
SELECT <projection> FROM "dojo_finding" ORDER BY "dojo_finding"."id" ASC LIMIT 100 OFFSET 500000
Limit  (cost=75627.06..75642.18 rows=100 width=5463) (actual rows=100.00 loops=1)
  Buffers: shared hit=14586 read=63958
  ->  Index Scan using dojo_finding_pkey on dojo_finding  (cost=0.42..151168.53 rows=999437 width=5463) (actual rows=500100.00 loops=1)
        Index Searches: 1
        Buffers: shared hit=14586 read=63958
Planning:
  Buffers: shared read=2
Planning Time: 0.217 ms
Execution Time: 358.883 ms
### findings_offset_500k: dojo_finding / 24890b89, observed 33.70 ms
SELECT <projection> FROM "dojo_finding"
Finalize Aggregate  (cost=17617.23..17617.24 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=23 read=4047
  ->  Gather  (cost=17617.01..17617.22 rows=2 width=8) (actual rows=3.00 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=23 read=4047
        ->  Partial Aggregate  (cost=16617.01..16617.02 rows=1 width=8) (actual rows=1.00 loops=3)
              Buffers: shared hit=23 read=4047
              ->  Parallel Index Only Scan using dojo_finding_reporter_id_dec2fe8c on dojo_finding  (cost=0.42..15575.93 rows=416432 width=0) (actual rows=333333.33 loops=3)
                    Heap Fetches: 26055
                    Index Searches: 1
                    Buffers: shared hit=23 read=4047
Planning:
  Buffers: shared read=4
Planning Time: 0.254 ms
Execution Time: 35.503 ms
{"case": "findings_fast_500k", "url": "/api/v2/findings/?limit=100&offset=500000&fast_offset=1", "status": 200, "sql_count": 25, "sql_ms": 51.353, "fetch_ms": 0, "django_ms": 269.853, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_finding / 24890b89": 1, "dojo_finding / b087ba0d": 1, "dojo_finding / 3bca1891": 1, "dojo_locationfindingreference / 7232ecb7": 1, "auth_user / c717d892": 1, "dojo_test_type / 9210c588": 1, "dojo_notes / 24579f35": 1, "dojo_risk_acceptance / 40c15205": 1, "dojo_test / ee10437d": 1, "dojo_tagulous_finding_tags / 6e492e55": 1, "dojo_jira_issue / b01edc2a": 1, "dojo_finding_group / baac0f4d": 1, "dojo_fileupload / dc5354fd": 1, "dojo_burprawrequestresponse / 4c41c852": 1, "dojo_endpoint_status / bd0088ca": 1, "dojo_dojometa / 0ad748ba": 1, "dojo_test_type / 7a604a36": 1, "dojo_engagement / 601e4b24": 1, "dojo_product / 14906c2b": 1, "dojo_product_type / d8070c78": 1, "dojo_finding_cwe / 8168aedd": 1, "dojo_findingvulnerabilityreference / 787dc19d": 1}, "bytes": 287148}
### findings_fast_500k: dojo_finding / 24890b89, observed 23.56 ms
SELECT <projection> FROM "dojo_finding"
Finalize Aggregate  (cost=17617.23..17617.24 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=4071
  ->  Gather  (cost=17617.01..17617.22 rows=2 width=8) (actual rows=3.00 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=4071
        ->  Partial Aggregate  (cost=16617.01..16617.02 rows=1 width=8) (actual rows=1.00 loops=3)
              Buffers: shared hit=4071
              ->  Parallel Index Only Scan using dojo_finding_reporter_id_dec2fe8c on dojo_finding  (cost=0.42..15575.93 rows=416432 width=0) (actual rows=333333.33 loops=3)
                    Heap Fetches: 26055
                    Index Searches: 1
                    Buffers: shared hit=4071
Planning:
  Buffers: shared hit=4
Planning Time: 0.133 ms
Execution Time: 29.215 ms
### findings_fast_500k: dojo_finding / b087ba0d, observed 19.41 ms
SELECT <projection> FROM "dojo_finding" ORDER BY "dojo_finding"."id" ASC LIMIT 100 OFFSET 500000
Limit  (cost=14625.47..14628.39 rows=100 width=4) (actual rows=100.00 loops=1)
  Buffers: shared hit=1409
  ->  Index Only Scan using dojo_finding_pkey on dojo_finding  (cost=0.42..29234.05 rows=999437 width=4) (actual rows=500100.00 loops=1)
        Heap Fetches: 0
        Index Searches: 1
        Buffers: shared hit=1409
Planning:
  Buffers: shared hit=2
Planning Time: 0.105 ms
Execution Time: 27.053 ms
{"case": "products", "url": "/api/v2/products/?limit=100", "status": 200, "sql_count": 10, "sql_ms": 889.323, "fetch_ms": 0, "django_ms": 979.565, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_product / 888bac19": 1, "dojo_product / d348b756": 1, "dojo_tagulous_product_tags / 0d949bb1": 1, "dojo_dojometa / b9c3a816": 1, "auth_user / 00777406": 1, "dojo_regulation / d339dab0": 1, "dojo_finding / 0a7c0e0e": 1}, "bytes": 5798301}
### products: dojo_finding / 0a7c0e0e, observed 885.75 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_finding"."active" AND "dojo_engagement"."product_id" IN (<parameters>)) GROUP BY 1
GroupAggregate  (cost=204247.05..208642.94 rows=7 width=36) (actual rows=12.00 loops=1)
  Group Key: dojo_engagement.product_id
  Buffers: shared hit=13752 read=111442, temp read=1859 written=1869
  ->  Sort  (cost=204247.05..205712.32 rows=586106 width=8) (actual rows=840282.00 loops=1)
        Sort Key: dojo_engagement.product_id, dojo_finding.id
        Sort Method: external merge  Disk: 14872kB
        Buffers: shared hit=13752 read=111442, temp read=1859 written=1869
        ->  Hash Join  (cost=14.43..140080.75 rows=586106 width=8) (actual rows=840282.00 loops=1)
              Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
              Buffers: shared hit=13752 read=111442
              ->  Hash Join  (cost=4.16..137484.46 rows=837295 width=8) (actual rows=840282.00 loops=1)
                    Hash Cond: (dojo_finding.test_id = dojo_test.id)
                    Buffers: shared hit=13751 read=111442
                    ->  Seq Scan on dojo_finding  (cost=0.00..135185.37 rows=837295 width=8) (actual rows=840282.00 loops=1)
                          Filter: active
                          Rows Removed by Filter: 159718
                          Buffers: shared hit=13749 read=111442
                    ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                          Buckets: 1024  Batches: 1  Memory Usage: 12kB
                          Buffers: shared hit=2
                          ->  Seq Scan on dojo_test  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                                Buffers: shared hit=2
              ->  Hash  (cost=10.18..10.18 rows=7 width=8) (actual rows=24.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 9kB
                    Buffers: shared hit=1
                    ->  Seq Scan on dojo_engagement  (cost=0.03..10.18 rows=7 width=8) (actual rows=24.00 loops=1)
                          Filter: (product_id = ANY ('?'::integer[]))
                          Buffers: shared hit=1
Planning:
  Buffers: shared hit=8
Planning Time: 0.476 ms
JIT:
  Functions: 28
  Options: Inlining false, Optimization false, Expressions true, Deforming true
Execution Time: 829.834 ms
{"case": "engagements", "url": "/api/v2/engagements/?limit=100", "status": 200, "sql_count": 9, "sql_ms": 2.747, "fetch_ms": 0, "django_ms": 16.988, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_engagement / 19d36082": 1, "dojo_engagement / 35986069": 1, "dojo_notes / f7768e16": 1, "dojo_risk_acceptance / 11a7aa68": 1, "dojo_fileupload / edb4abb7": 1, "dojo_tagulous_engagement_tags / 4fd8464a": 1}, "bytes": 20739}
{"case": "tests", "url": "/api/v2/tests/?limit=100", "status": 200, "sql_count": 9, "sql_ms": 3.766, "fetch_ms": 0, "django_ms": 35.324, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_test / 34915665": 1, "dojo_test / f651efd0": 1, "dojo_notes / c213cdc1": 1, "dojo_fileupload / 53abe2b5": 1, "dojo_tagulous_test_tags / 07086dd3": 1, "dojo_finding_group / 56062b6e": 1}, "bytes": 61461}
{"case": "products_filtered_heavy", "url": "/api/v2/products/?limit=1&id=2", "status": 200, "sql_count": 10, "sql_ms": 945.89, "fetch_ms": 0, "django_ms": 997.199, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_product / 2a592d23": 1, "dojo_product / 204c01f9": 1, "dojo_tagulous_product_tags / 07e72a97": 1, "dojo_dojometa / bf20f5e0": 1, "auth_user / 41271aed": 1, "dojo_regulation / 70ae594e": 1, "dojo_finding / 24240be4": 1}, "bytes": 3669627}
### products_filtered_heavy: dojo_finding / 24240be4, observed 941.91 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_finding"."active" AND "dojo_engagement"."product_id" IN (%s)) GROUP BY 1
GroupAggregate  (cost=58183.27..58601.94 rows=1 width=36) (actual rows=1.00 loops=1)
  Buffers: shared hit=3 read=422808, temp read=1178 written=1184
  ->  Sort  (cost=58183.27..58392.60 rows=83730 width=8) (actual rows=532569.00 loops=1)
        Sort Key: dojo_finding.id
        Sort Method: external merge  Disk: 9424kB
        Buffers: shared hit=3 read=422808, temp read=1178 written=1184
        ->  Nested Loop  (cost=115.02..51336.90 rows=83730 width=8) (actual rows=532569.00 loops=1)
              Buffers: shared hit=3 read=422808
              ->  Nested Loop  (cost=0.28..24.18 rows=10 width=8) (actual rows=8.00 loops=1)
                    Join Filter: (dojo_engagement.id = dojo_test.engagement_id)
                    Rows Removed by Join Filter: 180
                    Buffers: shared hit=3 read=2
                    ->  Index Scan using dojo_test_pkey on dojo_test  (cost=0.14..14.58 rows=96 width=8) (actual rows=96.00 loops=1)
                          Index Searches: 1
                          Buffers: shared hit=2 read=1
                    ->  Materialize  (cost=0.14..8.16 rows=1 width=8) (actual rows=1.96 loops=96)
                          Storage: Memory  Maximum Storage: 17kB
                          Buffers: shared hit=1 read=1
                          ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                                Index Cond: (product_id = 2)
                                Index Searches: 1
                                Buffers: shared hit=1 read=1
              ->  Bitmap Heap Scan on dojo_finding  (cost=114.74..5044.05 rows=8722 width=8) (actual rows=66571.12 loops=8)
                    Recheck Cond: ((dojo_test.id = test_id) AND active)
                    Heap Blocks: exact=422365
                    Buffers: shared read=422806
                    ->  Bitmap Index Scan on dojo_findin_test_id_bfc47c_idx  (cost=0.00..112.56 rows=8722 width=0) (actual rows=66571.12 loops=8)
                          Index Cond: ((test_id = dojo_test.id) AND (active = true))
                          Index Searches: 8
                          Buffers: shared read=441
Planning:
  Buffers: shared hit=3 read=5
Planning Time: 0.504 ms
Execution Time: 908.612 ms
{"case": "products_filtered_sparse", "url": "/api/v2/products/?limit=1&id=13", "status": 200, "sql_count": 10, "sql_ms": 64.341, "fetch_ms": 0, "django_ms": 76.723, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_product / 2a592d23": 1, "dojo_product / 204c01f9": 1, "dojo_tagulous_product_tags / 07e72a97": 1, "dojo_dojometa / bf20f5e0": 1, "auth_user / 41271aed": 1, "dojo_regulation / 70ae594e": 1, "dojo_finding / 24240be4": 1}, "bytes": 194686}
### products_filtered_sparse: dojo_finding / 24240be4, observed 61.28 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_finding"."active" AND "dojo_engagement"."product_id" IN (%s)) GROUP BY 1
GroupAggregate  (cost=58183.27..58601.94 rows=1 width=36) (actual rows=1.00 loops=1)
  Buffers: shared hit=2380 read=25436
  ->  Sort  (cost=58183.27..58392.60 rows=83730 width=8) (actual rows=28143.00 loops=1)
        Sort Key: dojo_finding.id
        Sort Method: quicksort  Memory: 1428kB
        Buffers: shared hit=2380 read=25436
        ->  Nested Loop  (cost=115.02..51336.90 rows=83730 width=8) (actual rows=28143.00 loops=1)
              Buffers: shared hit=2380 read=25436
              ->  Nested Loop  (cost=0.28..24.18 rows=10 width=8) (actual rows=8.00 loops=1)
                    Join Filter: (dojo_engagement.id = dojo_test.engagement_id)
                    Rows Removed by Join Filter: 180
                    Buffers: shared hit=3 read=2
                    ->  Index Scan using dojo_test_pkey on dojo_test  (cost=0.14..14.58 rows=96 width=8) (actual rows=96.00 loops=1)
                          Index Searches: 1
                          Buffers: shared hit=3
                    ->  Materialize  (cost=0.14..8.16 rows=1 width=8) (actual rows=1.96 loops=96)
                          Storage: Memory  Maximum Storage: 17kB
                          Buffers: shared read=2
                          ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                                Index Cond: (product_id = 13)
                                Index Searches: 1
                                Buffers: shared read=2
              ->  Bitmap Heap Scan on dojo_finding  (cost=114.74..5044.05 rows=8722 width=8) (actual rows=3517.88 loops=8)
                    Recheck Cond: ((dojo_test.id = test_id) AND active)
                    Heap Blocks: exact=27763
                    Buffers: shared hit=2377 read=25434
                    ->  Bitmap Index Scan on dojo_findin_test_id_bfc47c_idx  (cost=0.00..112.56 rows=8722 width=0) (actual rows=3517.88 loops=8)
                          Index Cond: ((test_id = dojo_test.id) AND (active = true))
                          Index Searches: 8
                          Buffers: shared hit=16 read=32
Planning:
  Buffers: shared hit=4 read=4
Planning Time: 0.399 ms
Execution Time: 65.076 ms
