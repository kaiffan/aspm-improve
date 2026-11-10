141 objects imported automatically (use -v 2 for details).

{"case": "findings", "url": "/api/v2/findings/?limit=100", "status": 200, "sql_count": 24, "sql_ms": 29.448, "django_ms": 207.31, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_finding / 24890b89": 1, "dojo_finding / 6f347a8b": 1, "dojo_locationfindingreference / 7232ecb7": 1, "auth_user / c717d892": 1, "dojo_test_type / 9210c588": 1, "dojo_notes / 24579f35": 1, "dojo_risk_acceptance / 40c15205": 1, "dojo_test / d61f5eb7": 1, "dojo_tagulous_finding_tags / 6e492e55": 1, "dojo_jira_issue / b01edc2a": 1, "dojo_finding_group / baac0f4d": 1, "dojo_fileupload / dc5354fd": 1, "dojo_burprawrequestresponse / 4c41c852": 1, "dojo_endpoint_status / bd0088ca": 1, "dojo_dojometa / 0ad748ba": 1, "dojo_test_type / 7a604a36": 1, "dojo_engagement / 5e7afcc8": 1, "dojo_product / 14906c2b": 1, "dojo_product_type / d8070c78": 1, "dojo_finding_cwe / 8168aedd": 1, "dojo_findingvulnerabilityreference / 787dc19d": 1}, "bytes": 283879}
### findings: dojo_finding / 24890b89, observed 21.25 ms
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
Planning Time: 0.118 ms
Execution Time: 29.285 ms
{"case": "finding_detail", "url": "/api/v2/findings/1000000/", "status": 200, "sql_count": 23, "sql_ms": 3.906, "django_ms": 21.795, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_finding / 5f6449df": 1, "dojo_locationfindingreference / 6aee1d80": 1, "auth_user / 2cd8f31a": 1, "dojo_test_type / 512424f1": 1, "dojo_notes / acb7902e": 1, "dojo_risk_acceptance / 1d462d15": 1, "dojo_test / 4c011d0e": 1, "dojo_tagulous_finding_tags / 86947250": 1, "dojo_jira_issue / b1f9f5d5": 1, "dojo_finding_group / 820c377b": 1, "dojo_fileupload / 741b65b7": 1, "dojo_burprawrequestresponse / eeee3915": 1, "dojo_endpoint_status / 36daf5b7": 1, "dojo_dojometa / fd816624": 1, "dojo_test_type / 7a604a36": 1, "dojo_engagement / 925456a2": 1, "dojo_product / b10d7cde": 1, "dojo_product_type / d8070c78": 1, "dojo_finding_cwe / bbae548e": 1, "dojo_findingvulnerabilityreference / 04792eed": 1}, "bytes": 3161}
{"case": "findings_high_active", "url": "/api/v2/findings/?limit=100&severity=High&active=true", "status": 200, "sql_count": 24, "sql_ms": 17.002, "django_ms": 111.926, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_finding / 543b893d": 1, "dojo_finding / aa426bce": 1, "dojo_locationfindingreference / 7232ecb7": 1, "auth_user / c717d892": 1, "dojo_test_type / 9210c588": 1, "dojo_notes / 24579f35": 1, "dojo_risk_acceptance / 40c15205": 1, "dojo_test / 5e049563": 1, "dojo_tagulous_finding_tags / 6e492e55": 1, "dojo_jira_issue / b01edc2a": 1, "dojo_finding_group / baac0f4d": 1, "dojo_fileupload / dc5354fd": 1, "dojo_burprawrequestresponse / 4c41c852": 1, "dojo_endpoint_status / bd0088ca": 1, "dojo_dojometa / 0ad748ba": 1, "dojo_test_type / 7a604a36": 1, "dojo_engagement / b6df710f": 1, "dojo_product / 14906c2b": 1, "dojo_product_type / d8070c78": 1, "dojo_finding_cwe / 8168aedd": 1, "dojo_findingvulnerabilityreference / 787dc19d": 1}, "bytes": 282342}
### findings_high_active: dojo_finding / 543b893d, observed 7.47 ms
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
Planning Time: 0.172 ms
Execution Time: 7.306 ms
{"case": "findings_offset_500k", "url": "/api/v2/findings/?limit=100&offset=500000", "status": 200, "sql_count": 24, "sql_ms": 612.8, "django_ms": 708.962, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_finding / 24890b89": 1, "dojo_finding / 74811f68": 1, "dojo_locationfindingreference / 7232ecb7": 1, "auth_user / c717d892": 1, "dojo_test_type / 9210c588": 1, "dojo_notes / 24579f35": 1, "dojo_risk_acceptance / 40c15205": 1, "dojo_test / ee10437d": 1, "dojo_tagulous_finding_tags / 6e492e55": 1, "dojo_jira_issue / b01edc2a": 1, "dojo_finding_group / baac0f4d": 1, "dojo_fileupload / dc5354fd": 1, "dojo_burprawrequestresponse / 4c41c852": 1, "dojo_endpoint_status / bd0088ca": 1, "dojo_dojometa / 0ad748ba": 1, "dojo_test_type / 7a604a36": 1, "dojo_engagement / 601e4b24": 1, "dojo_product / 14906c2b": 1, "dojo_product_type / d8070c78": 1, "dojo_finding_cwe / 8168aedd": 1, "dojo_findingvulnerabilityreference / 787dc19d": 1}, "bytes": 287120}
### findings_offset_500k: dojo_finding / 74811f68, observed 454.07 ms
SELECT <projection> FROM "dojo_finding" ORDER BY "dojo_finding"."id" ASC LIMIT 100 OFFSET 500000
Limit  (cost=75627.06..75642.18 rows=100 width=5463) (actual rows=100.00 loops=1)
  Buffers: shared hit=14586 read=63958
  ->  Index Scan using dojo_finding_pkey on dojo_finding  (cost=0.42..151168.53 rows=999437 width=5463) (actual rows=500100.00 loops=1)
        Index Searches: 1
        Buffers: shared hit=14586 read=63958
Planning:
  Buffers: shared read=2
Planning Time: 0.190 ms
Execution Time: 362.391 ms
### findings_offset_500k: dojo_finding / 24890b89, observed 148.32 ms
SELECT <projection> FROM "dojo_finding"
Finalize Aggregate  (cost=17617.23..17617.24 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=24 read=4047
  ->  Gather  (cost=17617.01..17617.22 rows=2 width=8) (actual rows=3.00 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=24 read=4047
        ->  Partial Aggregate  (cost=16617.01..16617.02 rows=1 width=8) (actual rows=1.00 loops=3)
              Buffers: shared hit=24 read=4047
              ->  Parallel Index Only Scan using dojo_finding_reporter_id_dec2fe8c on dojo_finding  (cost=0.42..15575.93 rows=416432 width=0) (actual rows=333333.33 loops=3)
                    Heap Fetches: 26055
                    Index Searches: 1
                    Buffers: shared hit=24 read=4047
Planning:
  Buffers: shared read=4
Planning Time: 0.262 ms
Execution Time: 36.417 ms
{"case": "findings_fast_500k", "url": "/api/v2/findings/?limit=100&offset=500000&fast_offset=1", "status": 200, "sql_count": 25, "sql_ms": 50.882, "django_ms": 286.635, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_finding / 24890b89": 1, "dojo_finding / b087ba0d": 1, "dojo_finding / 3bca1891": 1, "dojo_locationfindingreference / 7232ecb7": 1, "auth_user / c717d892": 1, "dojo_test_type / 9210c588": 1, "dojo_notes / 24579f35": 1, "dojo_risk_acceptance / 40c15205": 1, "dojo_test / ee10437d": 1, "dojo_tagulous_finding_tags / 6e492e55": 1, "dojo_jira_issue / b01edc2a": 1, "dojo_finding_group / baac0f4d": 1, "dojo_fileupload / dc5354fd": 1, "dojo_burprawrequestresponse / 4c41c852": 1, "dojo_endpoint_status / bd0088ca": 1, "dojo_dojometa / 0ad748ba": 1, "dojo_test_type / 7a604a36": 1, "dojo_engagement / 601e4b24": 1, "dojo_product / 14906c2b": 1, "dojo_product_type / d8070c78": 1, "dojo_finding_cwe / 8168aedd": 1, "dojo_findingvulnerabilityreference / 787dc19d": 1}, "bytes": 287148}
### findings_fast_500k: dojo_finding / 24890b89, observed 22.16 ms
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
Planning Time: 0.166 ms
Execution Time: 26.946 ms
### findings_fast_500k: dojo_finding / b087ba0d, observed 19.30 ms
SELECT <projection> FROM "dojo_finding" ORDER BY "dojo_finding"."id" ASC LIMIT 100 OFFSET 500000
Limit  (cost=14625.47..14628.39 rows=100 width=4) (actual rows=100.00 loops=1)
  Buffers: shared hit=1409
  ->  Index Only Scan using dojo_finding_pkey on dojo_finding  (cost=0.42..29234.05 rows=999437 width=4) (actual rows=500100.00 loops=1)
        Heap Fetches: 0
        Index Searches: 1
        Buffers: shared hit=1409
Planning:
  Buffers: shared hit=2
Planning Time: 0.322 ms
Execution Time: 26.824 ms
{"case": "products", "url": "/api/v2/products/?limit=100", "status": 200, "sql_count": 22, "sql_ms": 5410.194, "django_ms": 5582.836, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_finding / ccec2eea": 1, "dojo_finding / 7fa1d5b7": 1, "dojo_tagulous_product_tags / 0d949bb1": 1, "dojo_dojometa / b9c3a816": 1, "auth_user / 00777406": 1, "dojo_regulation / d339dab0": 1, "dojo_finding / a4a3dcaa": 13}, "bytes": 5798301}
### products: dojo_finding / 7fa1d5b7, observed 2002.85 ms
SELECT <projection> FROM "dojo_finding" U0 INNER JOIN "dojo_test" U1 ON (U0."test_id" = U1."id") INNER JOIN "dojo_engagement" U2 ON (U1."engagement_id" = U2."id") WHERE (U2."product_id" = ("dojo_product"."id") AND U0."active") GROUP BY U2."product_id" ORDER BY U2."product_id" ASC LIMIT 1), %s) AS "active_finding_count", "dojo_product_platform"."id", "dojo_product_platform"."value", "dojo_product_platform"."name", "dojo_product_platform"."icon", "dojo_product_platform"."display_order", "dojo_product_lifecycle"."id", "dojo_product_lifecycle"."value", "dojo_product_lifecycle"."name", "dojo_product_lifecycle"."icon", "dojo_product_lifecycle"."display_order", "dojo_product_origin"."id", "dojo_product_origin"."value", "dojo_product_origin"."name", "dojo_product_origin"."icon", "dojo_product_origin"."display_order" FROM "dojo_product" LEFT OUTER JOIN "dojo_product_platform" ON ("dojo_product"."platform_id" = "dojo_product_platform"."id") LEFT OUTER JOIN "dojo_product_lifecycle" ON ("dojo_product"."lifecycle_id" = "dojo_product_lifecycle"."id") LEFT OUTER JOIN "dojo_product_origin" ON ("dojo_product"."origin_id" = "dojo_product_origin"."id") ORDER BY "dojo_product"."name" ASC LIMIT 100
Limit  (cost=51535.59..3092135.97 rows=60 width=3475) (actual rows=13.00 loops=1)
  Buffers: shared hit=33195 read=694129
  ->  Unique  (cost=51535.59..3092135.97 rows=60 width=3475) (actual rows=13.00 loops=1)
        Buffers: shared hit=33195 read=694129
        ->  Incremental Sort  (cost=51535.59..3092129.52 rows=60 width=3475) (actual rows=13.00 loops=1)
              Sort Key: dojo_product.name, dojo_product.id, dojo_product.created, dojo_product.updated, dojo_product.description, dojo_product.product_manager_id, dojo_product.technical_contact_id, dojo_product.team_manager_id, dojo_product.prod_type_id, dojo_product.sla_configuration_id, dojo_product.tid, dojo_product.prod_numeric_grade, dojo_product.business_criticality, dojo_product.platform_id, dojo_product.lifecycle_id, dojo_product.origin_id, dojo_product.user_records, dojo_product.revenue, dojo_product.external_audience, dojo_product.internet_accessible, dojo_product.enable_product_tag_inheritance, dojo_product.enable_simple_risk_acceptance, dojo_product.enable_full_risk_acceptance, dojo_product.disable_sla_breach_notifications, dojo_product.async_updating, dojo_product.archived_at, dojo_product.archive_batch, (COALESCE((SubPlan 1), '?'::bigint)), dojo_product_platform.id, dojo_product_platform.value, dojo_product_platform.name, dojo_product_platform.icon, dojo_product_platform.display_order, dojo_product_lifecycle.id, dojo_product_lifecycle.value, dojo_product_lifecycle.name, dojo_product_lifecycle.icon, dojo_product_lifecycle.display_order, dojo_product_origin.id, dojo_product_origin.value, dojo_product_origin.name, dojo_product_origin.icon, dojo_product_origin.display_order
              Presorted Key: dojo_product.name
              Full-sort Groups: 1  Sort Method: quicksort  Average Memory: 27kB  Peak Memory: 27kB
              Buffers: shared hit=33195 read=694129
              ->  Nested Loop Left Join  (cost=0.14..3092126.82 rows=60 width=3475) (actual rows=13.00 loops=1)
                    Join Filter: (dojo_product.origin_id = dojo_product_origin.id)
                    Rows Removed by Join Filter: 74
                    Buffers: shared hit=33195 read=694129
                    ->  Nested Loop Left Join  (cost=0.14..58.27 rows=60 width=2705) (actual rows=13.00 loops=1)
                          Join Filter: (dojo_product.lifecycle_id = dojo_product_lifecycle.id)
                          Rows Removed by Join Filter: 37
                          Buffers: shared read=4
                          ->  Nested Loop Left Join  (cost=0.14..54.55 rows=60 width=1943) (actual rows=13.00 loops=1)
                                Join Filter: (dojo_product.platform_id = dojo_product_platform.id)
                                Rows Removed by Join Filter: 61
                                Buffers: shared read=3
                                ->  Index Scan using dojo_product_name_key on dojo_product  (cost=0.14..49.04 rows=60 width=1181) (actual rows=13.00 loops=1)
                                      Index Searches: 1
                                      Buffers: shared read=2
                                ->  Materialize  (cost=0.00..1.07 rows=5 width=762) (actual rows=4.77 loops=13)
                                      Storage: Memory  Maximum Storage: 17kB
                                      Buffers: shared read=1
                                      ->  Seq Scan on dojo_product_platform  (cost=0.00..1.05 rows=5 width=762) (actual rows=5.00 loops=1)
                                            Buffers: shared read=1
                          ->  Materialize  (cost=0.00..1.04 rows=3 width=762) (actual rows=2.92 loops=13)
                                Storage: Memory  Maximum Storage: 17kB
                                Buffers: shared read=1
                                ->  Seq Scan on dojo_product_lifecycle  (cost=0.00..1.03 rows=3 width=762) (actual rows=3.00 loops=1)
                                      Buffers: shared read=1
                    ->  Materialize  (cost=0.00..1.09 rows=6 width=762) (actual rows=5.77 loops=13)
                          Storage: Memory  Maximum Storage: 17kB
                          Buffers: shared read=1
                          ->  Seq Scan on dojo_product_origin  (cost=0.00..1.06 rows=6 width=762) (actual rows=6.00 loops=1)
                                Buffers: shared read=1
                    SubPlan 1
                      ->  Limit  (cost=114.88..51534.37 rows=1 width=12) (actual rows=0.92 loops=13)
                            Buffers: shared hit=33195 read=694124
                            ->  GroupAggregate  (cost=114.88..51534.37 rows=1 width=12) (actual rows=0.92 loops=13)
                                  Buffers: shared hit=33195 read=694124
                                  ->  Nested Loop  (cost=114.88..51325.03 rows=83730 width=8) (actual rows=64637.08 loops=13)
                                        Buffers: shared hit=33195 read=694124
                                        ->  Nested Loop  (cost=0.14..12.31 rows=10 width=8) (actual rows=7.38 loops=13)
                                              Join Filter: (u2.id = u1.engagement_id)
                                              Rows Removed by Join Filter: 170
                                              Buffers: shared hit=60 read=13
                                              ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement u2  (cost=0.14..8.15 rows=1 width=8) (actual rows=1.85 loops=13)
                                                    Index Cond: (product_id = dojo_product.id)
                                                    Index Searches: 13
                                                    Buffers: shared hit=12 read=13
                                              ->  Seq Scan on dojo_test u1  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=24)
                                                    Buffers: shared hit=48
                                        ->  Bitmap Heap Scan on dojo_finding u0  (cost=114.74..5044.05 rows=8722 width=8) (actual rows=8752.94 loops=96)
                                              Recheck Cond: ((u1.id = test_id) AND active)
                                              Heap Blocks: exact=726277
                                              Buffers: shared hit=33135 read=694111
                                              ->  Bitmap Index Scan on dojo_findin_test_id_bfc47c_idx  (cost=0.00..112.56 rows=8722 width=0) (actual rows=8752.94 loops=96)
                                                    Index Cond: ((test_id = u1.id) AND (active = true))
                                                    Index Searches: 96
                                                    Buffers: shared hit=174 read=795
Planning:
  Buffers: shared hit=2 read=7
Planning Time: 1.328 ms
JIT:
  Functions: 33
  Options: Inlining true, Optimization true, Expressions true, Deforming true
Execution Time: 1939.028 ms
### products: dojo_finding / ccec2eea, observed 1733.88 ms
SELECT <projection> FROM (SELECT DISTINCT "dojo_product"."id" AS "col1", "dojo_product"."created" AS "col2", "dojo_product"."updated" AS "col3", "dojo_product"."name" AS "col4", "dojo_product"."description" AS "col5", "dojo_product"."product_manager_id" AS "col6", "dojo_product"."technical_contact_id" AS "col7", "dojo_product"."team_manager_id" AS "col8", "dojo_product"."prod_type_id" AS "col9", "dojo_product"."sla_configuration_id" AS "col10", "dojo_product"."tid" AS "col11", "dojo_product"."prod_numeric_grade" AS "col12", "dojo_product"."business_criticality" AS "col13", "dojo_product"."platform_id" AS "col14", "dojo_product"."lifecycle_id" AS "col15", "dojo_product"."origin_id" AS "col16", "dojo_product"."user_records" AS "col17", "dojo_product"."revenue" AS "col18", "dojo_product"."external_audience" AS "col19", "dojo_product"."internet_accessible" AS "col20", "dojo_product"."enable_product_tag_inheritance" AS "col21", "dojo_product"."enable_simple_risk_acceptance" AS "col22", "dojo_product"."enable_full_risk_acceptance" AS "col23", "dojo_product"."disable_sla_breach_notifications" AS "col24", "dojo_product"."async_updating" AS "col25", "dojo_product"."archived_at" AS "col26", "dojo_product"."archive_batch" AS "col27", COALESCE((SELECT COUNT(U0."id") AS "c" FROM "dojo_finding" U0 INNER JOIN "dojo_test" U1 ON (U0."test_id" = U1."id") INNER JOIN "dojo_engagement" U2 ON (U1."e
Aggregate  (cost=3092118.83..3092118.84 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=33197 read=694124
  ->  Unique  (cost=51535.33..3092118.08 rows=60 width=1189) (actual rows=13.00 loops=1)
        Buffers: shared hit=33197 read=694124
        ->  Incremental Sort  (cost=51535.33..3092113.88 rows=60 width=1189) (actual rows=13.00 loops=1)
              Sort Key: dojo_product.technical_contact_id, dojo_product.id, dojo_product.created, dojo_product.updated, dojo_product.name, dojo_product.description, dojo_product.product_manager_id, dojo_product.team_manager_id, dojo_product.prod_type_id, dojo_product.sla_configuration_id, dojo_product.tid, dojo_product.prod_numeric_grade, dojo_product.business_criticality, dojo_product.platform_id, dojo_product.lifecycle_id, dojo_product.origin_id, dojo_product.user_records, dojo_product.revenue, dojo_product.external_audience, dojo_product.internet_accessible, dojo_product.enable_product_tag_inheritance, dojo_product.enable_simple_risk_acceptance, dojo_product.enable_full_risk_acceptance, dojo_product.disable_sla_breach_notifications, dojo_product.async_updating, dojo_product.archived_at, dojo_product.archive_batch, (COALESCE((SubPlan 1), '?'::bigint))
              Presorted Key: dojo_product.technical_contact_id
              Full-sort Groups: 1  Sort Method: quicksort  Average Memory: 26kB  Peak Memory: 26kB
              Buffers: shared hit=33197 read=694124
              ->  Index Scan using dojo_product_technical_contact_id_b85df8dd on dojo_product  (cost=0.14..3092111.18 rows=60 width=1189) (actual rows=13.00 loops=1)
                    Index Searches: 1
                    Buffers: shared hit=33197 read=694124
                    SubPlan 1
                      ->  Limit  (cost=114.88..51534.37 rows=1 width=12) (actual rows=0.92 loops=13)
                            Buffers: shared hit=33196 read=694123
                            ->  GroupAggregate  (cost=114.88..51534.37 rows=1 width=12) (actual rows=0.92 loops=13)
                                  Buffers: shared hit=33196 read=694123
                                  ->  Nested Loop  (cost=114.88..51325.03 rows=83730 width=8) (actual rows=64637.08 loops=13)
                                        Buffers: shared hit=33196 read=694123
                                        ->  Nested Loop  (cost=0.14..12.31 rows=10 width=8) (actual rows=7.38 loops=13)
                                              Join Filter: (u2.id = u1.engagement_id)
                                              Rows Removed by Join Filter: 170
                                              Buffers: shared hit=61 read=12
                                              ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement u2  (cost=0.14..8.15 rows=1 width=8) (actual rows=1.85 loops=13)
                                                    Index Cond: (product_id = dojo_product.id)
                                                    Index Searches: 13
                                                    Buffers: shared hit=13 read=12
                                              ->  Seq Scan on dojo_test u1  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=24)
                                                    Buffers: shared hit=48
                                        ->  Bitmap Heap Scan on dojo_finding u0  (cost=114.74..5044.05 rows=8722 width=8) (actual rows=8752.94 loops=96)
                                              Recheck Cond: ((u1.id = test_id) AND active)
                                              Heap Blocks: exact=726277
                                              Buffers: shared hit=33135 read=694111
                                              ->  Bitmap Index Scan on dojo_findin_test_id_bfc47c_idx  (cost=0.00..112.56 rows=8722 width=0) (actual rows=8752.94 loops=96)
                                                    Index Cond: ((test_id = u1.id) AND (active = true))
                                                    Index Searches: 96
                                                    Buffers: shared hit=174 read=795
Planning:
  Buffers: shared hit=3 read=6
Planning Time: 0.605 ms
JIT:
  Functions: 22
  Options: Inlining true, Optimization true, Expressions true, Deforming true
Execution Time: 1748.517 ms
### products: dojo_finding / a4a3dcaa, observed 918.70 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_finding"."active" AND "dojo_engagement"."product_id" = %s) ORDER BY 1 ASC
Sort  (cost=58183.27..58392.60 rows=83730 width=4) (actual rows=532569.00 loops=1)
  Sort Key: dojo_finding.id
  Sort Method: external merge  Disk: 6272kB
  Buffers: shared hit=852 read=421959, temp read=784 written=787
  ->  Nested Loop  (cost=115.02..51336.90 rows=83730 width=4) (actual rows=532569.00 loops=1)
        Buffers: shared hit=852 read=421959
        ->  Nested Loop  (cost=0.28..24.18 rows=10 width=4) (actual rows=8.00 loops=1)
              Join Filter: (dojo_engagement.id = dojo_test.engagement_id)
              Rows Removed by Join Filter: 180
              Buffers: shared hit=3 read=2
              ->  Index Scan using dojo_test_pkey on dojo_test  (cost=0.14..14.58 rows=96 width=8) (actual rows=96.00 loops=1)
                    Index Searches: 1
                    Buffers: shared hit=2 read=1
              ->  Materialize  (cost=0.14..8.16 rows=1 width=4) (actual rows=1.96 loops=96)
                    Storage: Memory  Maximum Storage: 17kB
                    Buffers: shared hit=1 read=1
                    ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                          Index Cond: (product_id = 2)
                          Index Searches: 1
                          Buffers: shared hit=1 read=1
        ->  Bitmap Heap Scan on dojo_finding  (cost=114.74..5044.05 rows=8722 width=8) (actual rows=66571.12 loops=8)
              Recheck Cond: ((dojo_test.id = test_id) AND active)
              Heap Blocks: exact=422365
              Buffers: shared hit=849 read=421957
              ->  Bitmap Index Scan on dojo_findin_test_id_bfc47c_idx  (cost=0.00..112.56 rows=8722 width=0) (actual rows=66571.12 loops=8)
                    Index Cond: ((test_id = dojo_test.id) AND (active = true))
                    Index Searches: 8
                    Buffers: shared hit=1 read=440
Planning:
  Buffers: shared hit=3 read=5
Planning Time: 0.404 ms
Execution Time: 862.898 ms
{"case": "engagements", "url": "/api/v2/engagements/?limit=100", "status": 200, "sql_count": 9, "sql_ms": 2.604, "django_ms": 16.265, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_engagement / 19d36082": 1, "dojo_engagement / 35986069": 1, "dojo_notes / f7768e16": 1, "dojo_risk_acceptance / 11a7aa68": 1, "dojo_fileupload / edb4abb7": 1, "dojo_tagulous_engagement_tags / 4fd8464a": 1}, "bytes": 20739}
{"case": "tests", "url": "/api/v2/tests/?limit=100", "status": 200, "sql_count": 9, "sql_ms": 3.592, "django_ms": 36.26, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_test / 34915665": 1, "dojo_test / f651efd0": 1, "dojo_notes / c213cdc1": 1, "dojo_fileupload / 53abe2b5": 1, "dojo_tagulous_test_tags / 07086dd3": 1, "dojo_finding_group / 56062b6e": 1}, "bytes": 61461}
