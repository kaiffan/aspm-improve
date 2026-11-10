141 objects imported automatically (use -v 2 for details).

{"case": "product_detail_large", "url": "/api/v2/products/2/", "status": 200, "sql_count": 9, "sql_ms": 1896.782, "fetch_ms": 0, "django_ms": 2005.274, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_finding / d5b9a974": 1, "dojo_tagulous_product_tags / 07e72a97": 1, "dojo_dojometa / bf20f5e0": 1, "auth_user / 41271aed": 1, "dojo_regulation / 70ae594e": 1, "dojo_finding / a4a3dcaa": 1}, "bytes": 3669575, "rows": 1}
### product_detail_large: dojo_finding / a4a3dcaa, observed 1066.40 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_finding"."active" AND "dojo_engagement"."product_id" = %s) ORDER BY 1 ASC
Sort  (cost=58183.27..58392.60 rows=83730 width=4) (actual rows=532569.00 loops=1)
  Sort Key: dojo_finding.id
  Sort Method: external merge  Disk: 6272kB
  Buffers: shared hit=3 read=422808, temp read=784 written=787
  ->  Nested Loop  (cost=115.02..51336.90 rows=83730 width=4) (actual rows=532569.00 loops=1)
        Buffers: shared hit=3 read=422808
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
              Buffers: shared read=422806
              ->  Bitmap Index Scan on dojo_findin_test_id_bfc47c_idx  (cost=0.00..112.56 rows=8722 width=0) (actual rows=66571.12 loops=8)
                    Index Cond: ((test_id = dojo_test.id) AND (active = true))
                    Index Searches: 8
                    Buffers: shared read=441
Planning:
  Buffers: shared hit=3 read=5
Planning Time: 0.904 ms
Execution Time: 910.937 ms
### product_detail_large: dojo_finding / d5b9a974, observed 827.53 ms
SELECT <projection> FROM "dojo_finding" U0 INNER JOIN "dojo_test" U1 ON (U0."test_id" = U1."id") INNER JOIN "dojo_engagement" U2 ON (U1."engagement_id" = U2."id") WHERE (U0."active" AND U2."product_id" = ("dojo_product"."id")) GROUP BY U2."product_id" ORDER BY U2."product_id" ASC LIMIT 1), %s) AS "active_finding_count", "dojo_product_platform"."id", "dojo_product_platform"."value", "dojo_product_platform"."name", "dojo_product_platform"."icon", "dojo_product_platform"."display_order", "dojo_product_lifecycle"."id", "dojo_product_lifecycle"."value", "dojo_product_lifecycle"."name", "dojo_product_lifecycle"."icon", "dojo_product_lifecycle"."display_order", "dojo_product_origin"."id", "dojo_product_origin"."value", "dojo_product_origin"."name", "dojo_product_origin"."icon", "dojo_product_origin"."display_order" FROM "dojo_product" LEFT OUTER JOIN "dojo_product_platform" ON ("dojo_product"."platform_id" = "dojo_product_platform"."id") LEFT OUTER JOIN "dojo_product_lifecycle" ON ("dojo_product"."lifecycle_id" = "dojo_product_lifecycle"."id") LEFT OUTER JOIN "dojo_product_origin" ON ("dojo_product"."origin_id" = "dojo_product_origin"."id") WHERE "dojo_product"."id" = %s LIMIT 21
Limit  (cost=51545.85..51545.96 rows=1 width=3475) (actual rows=1.00 loops=1)
  Buffers: shared hit=5 read=422812
  ->  Unique  (cost=51545.85..51545.96 rows=1 width=3475) (actual rows=1.00 loops=1)
        Buffers: shared hit=5 read=422812
        ->  Sort  (cost=51545.85..51545.86 rows=1 width=3475) (actual rows=1.00 loops=1)
              Sort Key: dojo_product.created, dojo_product.updated, dojo_product.name, dojo_product.description, dojo_product.product_manager_id, dojo_product.technical_contact_id, dojo_product.team_manager_id, dojo_product.prod_type_id, dojo_product.sla_configuration_id, dojo_product.tid, dojo_product.prod_numeric_grade, dojo_product.business_criticality, dojo_product.platform_id, dojo_product.lifecycle_id, dojo_product.origin_id, dojo_product.user_records, dojo_product.revenue, dojo_product.external_audience, dojo_product.internet_accessible, dojo_product.enable_product_tag_inheritance, dojo_product.enable_simple_risk_acceptance, dojo_product.enable_full_risk_acceptance, dojo_product.disable_sla_breach_notifications, dojo_product.async_updating, dojo_product.archived_at, dojo_product.archive_batch, (COALESCE((SubPlan 1), '?'::bigint)), dojo_product_platform.id, dojo_product_platform.value, dojo_product_platform.name, dojo_product_platform.icon, dojo_product_platform.display_order, dojo_product_lifecycle.id, dojo_product_lifecycle.value, dojo_product_lifecycle.name, dojo_product_lifecycle.icon, dojo_product_lifecycle.display_order, dojo_product_origin.id, dojo_product_origin.value, dojo_product_origin.name, dojo_product_origin.icon, dojo_product_origin.display_order
              Sort Method: quicksort  Memory: 25kB
              Buffers: shared hit=5 read=422812
              ->  Nested Loop Left Join  (cost=0.14..51545.84 rows=1 width=3475) (actual rows=1.00 loops=1)
                    Join Filter: (dojo_product.origin_id = dojo_product_origin.id)
                    Rows Removed by Join Filter: 6
                    Buffers: shared hit=5 read=422812
                    ->  Nested Loop Left Join  (cost=0.14..10.34 rows=1 width=2705) (actual rows=1.00 loops=1)
                          Join Filter: (dojo_product.lifecycle_id = dojo_product_lifecycle.id)
                          Rows Removed by Join Filter: 3
                          Buffers: shared read=4
                          ->  Nested Loop Left Join  (cost=0.14..9.27 rows=1 width=1943) (actual rows=1.00 loops=1)
                                Join Filter: (dojo_product.platform_id = dojo_product_platform.id)
                                Rows Removed by Join Filter: 5
                                Buffers: shared read=3
                                ->  Index Scan using dojo_product_pkey on dojo_product  (cost=0.14..8.16 rows=1 width=1181) (actual rows=1.00 loops=1)
                                      Index Cond: (id = 2)
                                      Index Searches: 1
                                      Buffers: shared read=2
                                ->  Seq Scan on dojo_product_platform  (cost=0.00..1.05 rows=5 width=762) (actual rows=5.00 loops=1)
                                      Buffers: shared read=1
                          ->  Seq Scan on dojo_product_lifecycle  (cost=0.00..1.03 rows=3 width=762) (actual rows=3.00 loops=1)
                                Buffers: shared read=1
                    ->  Seq Scan on dojo_product_origin  (cost=0.00..1.06 rows=6 width=762) (actual rows=6.00 loops=1)
                          Buffers: shared read=1
                    SubPlan 1
                      ->  Limit  (cost=114.88..51534.37 rows=1 width=12) (actual rows=1.00 loops=1)
                            Buffers: shared hit=5 read=422807
                            ->  GroupAggregate  (cost=114.88..51534.37 rows=1 width=12) (actual rows=1.00 loops=1)
                                  Buffers: shared hit=5 read=422807
                                  ->  Nested Loop  (cost=114.88..51325.03 rows=83730 width=8) (actual rows=532569.00 loops=1)
                                        Buffers: shared hit=5 read=422807
                                        ->  Nested Loop  (cost=0.14..12.31 rows=10 width=8) (actual rows=8.00 loops=1)
                                              Join Filter: (u2.id = u1.engagement_id)
                                              Rows Removed by Join Filter: 184
                                              Buffers: shared hit=5 read=1
                                              ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement u2  (cost=0.14..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                                                    Index Cond: (product_id = dojo_product.id)
                                                    Index Searches: 1
                                                    Buffers: shared hit=1 read=1
                                              ->  Seq Scan on dojo_test u1  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=2)
                                                    Buffers: shared hit=4
                                        ->  Bitmap Heap Scan on dojo_finding u0  (cost=114.74..5044.05 rows=8722 width=8) (actual rows=66571.12 loops=8)
                                              Recheck Cond: ((u1.id = test_id) AND active)
                                              Heap Blocks: exact=422365
                                              Buffers: shared read=422806
                                              ->  Bitmap Index Scan on dojo_findin_test_id_bfc47c_idx  (cost=0.00..112.56 rows=8722 width=0) (actual rows=66571.12 loops=8)
                                                    Index Cond: ((test_id = u1.id) AND (active = true))
                                                    Index Searches: 8
                                                    Buffers: shared read=441
Planning:
  Buffers: shared hit=3 read=6
Planning Time: 1.244 ms
Execution Time: 816.127 ms
### product_detail_large: dojo_tagulous_product_tags / 07e72a97, observed 0.50 ms
SELECT <projection> FROM "dojo_tagulous_product_tags" INNER JOIN "dojo_product_tags" ON ("dojo_tagulous_product_tags"."id" = "dojo_product_tags"."tagulous_product_tags_id") WHERE "dojo_product_tags"."product_id" IN (%s) ORDER BY "dojo_tagulous_product_tags"."name" ASC
Sort  (cost=26.60..26.63 rows=10 width=647) (actual rows=0.00 loops=1)
  Sort Key: dojo_tagulous_product_tags.name
  Sort Method: quicksort  Memory: 25kB
  ->  Hash Join  (cost=14.91..26.44 rows=10 width=647) (actual rows=0.00 loops=1)
        Hash Cond: (dojo_tagulous_product_tags.id = dojo_product_tags.tagulous_product_tags_id)
        ->  Seq Scan on dojo_tagulous_product_tags  (cost=0.00..11.20 rows=120 width=643) (actual rows=0.00 loops=1)
        ->  Hash  (cost=14.79..14.79 rows=10 width=8) (never executed)
              ->  Bitmap Heap Scan on dojo_product_tags  (cost=4.23..14.79 rows=10 width=8) (never executed)
                    Recheck Cond: (product_id = 2)
                    ->  Bitmap Index Scan on dojo_product_tags_product_id_4d5f12d3  (cost=0.00..4.23 rows=10 width=0) (never executed)
                          Index Cond: (product_id = 2)
                          Index Searches: 0
Planning:
  Buffers: shared read=10
Planning Time: 0.170 ms
Execution Time: 0.083 ms
{"case": "product_detail_sparse", "url": "/api/v2/products/13/", "status": 200, "sql_count": 9, "sql_ms": 167.007, "fetch_ms": 0, "django_ms": 184.984, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_finding / d5b9a974": 1, "dojo_tagulous_product_tags / 07e72a97": 1, "dojo_dojometa / bf20f5e0": 1, "auth_user / 41271aed": 1, "dojo_regulation / 70ae594e": 1, "dojo_finding / a4a3dcaa": 1}, "bytes": 194634, "rows": 1}
### product_detail_sparse: dojo_finding / a4a3dcaa, observed 103.83 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_finding"."active" AND "dojo_engagement"."product_id" = %s) ORDER BY 1 ASC
Sort  (cost=58183.27..58392.60 rows=83730 width=4) (actual rows=28143.00 loops=1)
  Sort Key: dojo_finding.id
  Sort Method: quicksort  Memory: 769kB
  Buffers: shared hit=2433 read=25383
  ->  Nested Loop  (cost=115.02..51336.90 rows=83730 width=4) (actual rows=28143.00 loops=1)
        Buffers: shared hit=2433 read=25383
        ->  Nested Loop  (cost=0.28..24.18 rows=10 width=4) (actual rows=8.00 loops=1)
              Join Filter: (dojo_engagement.id = dojo_test.engagement_id)
              Rows Removed by Join Filter: 180
              Buffers: shared hit=4 read=1
              ->  Index Scan using dojo_test_pkey on dojo_test  (cost=0.14..14.58 rows=96 width=8) (actual rows=96.00 loops=1)
                    Index Searches: 1
                    Buffers: shared hit=3
              ->  Materialize  (cost=0.14..8.16 rows=1 width=4) (actual rows=1.96 loops=96)
                    Storage: Memory  Maximum Storage: 17kB
                    Buffers: shared hit=1 read=1
                    ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                          Index Cond: (product_id = 13)
                          Index Searches: 1
                          Buffers: shared hit=1 read=1
        ->  Bitmap Heap Scan on dojo_finding  (cost=114.74..5044.05 rows=8722 width=8) (actual rows=3517.88 loops=8)
              Recheck Cond: ((dojo_test.id = test_id) AND active)
              Heap Blocks: exact=27763
              Buffers: shared hit=2429 read=25382
              ->  Bitmap Index Scan on dojo_findin_test_id_bfc47c_idx  (cost=0.00..112.56 rows=8722 width=0) (actual rows=3517.88 loops=8)
                    Index Cond: ((test_id = dojo_test.id) AND (active = true))
                    Index Searches: 8
                    Buffers: shared hit=16 read=32
Planning:
  Buffers: shared hit=4 read=4
Planning Time: 0.710 ms
Execution Time: 130.123 ms
### product_detail_sparse: dojo_finding / d5b9a974, observed 60.90 ms
SELECT <projection> FROM "dojo_finding" U0 INNER JOIN "dojo_test" U1 ON (U0."test_id" = U1."id") INNER JOIN "dojo_engagement" U2 ON (U1."engagement_id" = U2."id") WHERE (U0."active" AND U2."product_id" = ("dojo_product"."id")) GROUP BY U2."product_id" ORDER BY U2."product_id" ASC LIMIT 1), %s) AS "active_finding_count", "dojo_product_platform"."id", "dojo_product_platform"."value", "dojo_product_platform"."name", "dojo_product_platform"."icon", "dojo_product_platform"."display_order", "dojo_product_lifecycle"."id", "dojo_product_lifecycle"."value", "dojo_product_lifecycle"."name", "dojo_product_lifecycle"."icon", "dojo_product_lifecycle"."display_order", "dojo_product_origin"."id", "dojo_product_origin"."value", "dojo_product_origin"."name", "dojo_product_origin"."icon", "dojo_product_origin"."display_order" FROM "dojo_product" LEFT OUTER JOIN "dojo_product_platform" ON ("dojo_product"."platform_id" = "dojo_product_platform"."id") LEFT OUTER JOIN "dojo_product_lifecycle" ON ("dojo_product"."lifecycle_id" = "dojo_product_lifecycle"."id") LEFT OUTER JOIN "dojo_product_origin" ON ("dojo_product"."origin_id" = "dojo_product_origin"."id") WHERE "dojo_product"."id" = %s LIMIT 21
Limit  (cost=51545.85..51545.96 rows=1 width=3475) (actual rows=1.00 loops=1)
  Buffers: shared hit=2424 read=25398
  ->  Unique  (cost=51545.85..51545.96 rows=1 width=3475) (actual rows=1.00 loops=1)
        Buffers: shared hit=2424 read=25398
        ->  Sort  (cost=51545.85..51545.86 rows=1 width=3475) (actual rows=1.00 loops=1)
              Sort Key: dojo_product.created, dojo_product.updated, dojo_product.name, dojo_product.description, dojo_product.product_manager_id, dojo_product.technical_contact_id, dojo_product.team_manager_id, dojo_product.prod_type_id, dojo_product.sla_configuration_id, dojo_product.tid, dojo_product.prod_numeric_grade, dojo_product.business_criticality, dojo_product.platform_id, dojo_product.lifecycle_id, dojo_product.origin_id, dojo_product.user_records, dojo_product.revenue, dojo_product.external_audience, dojo_product.internet_accessible, dojo_product.enable_product_tag_inheritance, dojo_product.enable_simple_risk_acceptance, dojo_product.enable_full_risk_acceptance, dojo_product.disable_sla_breach_notifications, dojo_product.async_updating, dojo_product.archived_at, dojo_product.archive_batch, (COALESCE((SubPlan 1), '?'::bigint)), dojo_product_platform.id, dojo_product_platform.value, dojo_product_platform.name, dojo_product_platform.icon, dojo_product_platform.display_order, dojo_product_lifecycle.id, dojo_product_lifecycle.value, dojo_product_lifecycle.name, dojo_product_lifecycle.icon, dojo_product_lifecycle.display_order, dojo_product_origin.id, dojo_product_origin.value, dojo_product_origin.name, dojo_product_origin.icon, dojo_product_origin.display_order
              Sort Method: quicksort  Memory: 25kB
              Buffers: shared hit=2424 read=25398
              ->  Nested Loop Left Join  (cost=0.14..51545.84 rows=1 width=3475) (actual rows=1.00 loops=1)
                    Join Filter: (dojo_product.origin_id = dojo_product_origin.id)
                    Rows Removed by Join Filter: 6
                    Buffers: shared hit=2424 read=25398
                    ->  Nested Loop Left Join  (cost=0.14..10.34 rows=1 width=2705) (actual rows=1.00 loops=1)
                          Join Filter: (dojo_product.lifecycle_id = dojo_product_lifecycle.id)
                          Rows Removed by Join Filter: 3
                          Buffers: shared read=4
                          ->  Nested Loop Left Join  (cost=0.14..9.27 rows=1 width=1943) (actual rows=1.00 loops=1)
                                Join Filter: (dojo_product.platform_id = dojo_product_platform.id)
                                Rows Removed by Join Filter: 5
                                Buffers: shared read=3
                                ->  Index Scan using dojo_product_pkey on dojo_product  (cost=0.14..8.16 rows=1 width=1181) (actual rows=1.00 loops=1)
                                      Index Cond: (id = 13)
                                      Index Searches: 1
                                      Buffers: shared read=2
                                ->  Seq Scan on dojo_product_platform  (cost=0.00..1.05 rows=5 width=762) (actual rows=5.00 loops=1)
                                      Buffers: shared read=1
                          ->  Seq Scan on dojo_product_lifecycle  (cost=0.00..1.03 rows=3 width=762) (actual rows=3.00 loops=1)
                                Buffers: shared read=1
                    ->  Seq Scan on dojo_product_origin  (cost=0.00..1.06 rows=6 width=762) (actual rows=6.00 loops=1)
                          Buffers: shared read=1
                    SubPlan 1
                      ->  Limit  (cost=114.88..51534.37 rows=1 width=12) (actual rows=1.00 loops=1)
                            Buffers: shared hit=2424 read=25393
                            ->  GroupAggregate  (cost=114.88..51534.37 rows=1 width=12) (actual rows=1.00 loops=1)
                                  Buffers: shared hit=2424 read=25393
                                  ->  Nested Loop  (cost=114.88..51325.03 rows=83730 width=8) (actual rows=28143.00 loops=1)
                                        Buffers: shared hit=2424 read=25393
                                        ->  Nested Loop  (cost=0.14..12.31 rows=10 width=8) (actual rows=8.00 loops=1)
                                              Join Filter: (u2.id = u1.engagement_id)
                                              Rows Removed by Join Filter: 184
                                              Buffers: shared hit=4 read=2
                                              ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement u2  (cost=0.14..8.15 rows=1 width=8) (actual rows=2.00 loops=1)
                                                    Index Cond: (product_id = dojo_product.id)
                                                    Index Searches: 1
                                                    Buffers: shared read=2
                                              ->  Seq Scan on dojo_test u1  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=2)
                                                    Buffers: shared hit=4
                                        ->  Bitmap Heap Scan on dojo_finding u0  (cost=114.74..5044.05 rows=8722 width=8) (actual rows=3517.88 loops=8)
                                              Recheck Cond: ((u1.id = test_id) AND active)
                                              Heap Blocks: exact=27763
                                              Buffers: shared hit=2420 read=25391
                                              ->  Bitmap Index Scan on dojo_findin_test_id_bfc47c_idx  (cost=0.00..112.56 rows=8722 width=0) (actual rows=3517.88 loops=8)
                                                    Index Cond: ((test_id = u1.id) AND (active = true))
                                                    Index Searches: 8
                                                    Buffers: shared hit=16 read=32
Planning:
  Buffers: shared hit=3 read=6
Planning Time: 1.391 ms
Execution Time: 59.646 ms
{"case": "products_sparse", "url": "/api/v2/products/?id=13&limit=1", "status": 200, "sql_count": 10, "sql_ms": 69.083, "fetch_ms": 0, "django_ms": 81.752, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_product / 2a592d23": 1, "dojo_product / 204c01f9": 1, "dojo_tagulous_product_tags / 07e72a97": 1, "dojo_dojometa / bf20f5e0": 1, "auth_user / 41271aed": 1, "dojo_regulation / 70ae594e": 1, "dojo_finding / 24240be4": 1}, "bytes": 194686, "rows": 1}
### products_sparse: dojo_finding / 24240be4, observed 65.85 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_finding"."active" AND "dojo_engagement"."product_id" IN (%s)) GROUP BY 1
GroupAggregate  (cost=58183.27..58601.94 rows=1 width=36) (actual rows=1.00 loops=1)
  Buffers: shared hit=2382 read=25434
  ->  Sort  (cost=58183.27..58392.60 rows=83730 width=8) (actual rows=28143.00 loops=1)
        Sort Key: dojo_finding.id
        Sort Method: quicksort  Memory: 1428kB
        Buffers: shared hit=2382 read=25434
        ->  Nested Loop  (cost=115.02..51336.90 rows=83730 width=8) (actual rows=28143.00 loops=1)
              Buffers: shared hit=2382 read=25434
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
                    Buffers: shared hit=2379 read=25432
                    ->  Bitmap Index Scan on dojo_findin_test_id_bfc47c_idx  (cost=0.00..112.56 rows=8722 width=0) (actual rows=3517.88 loops=8)
                          Index Cond: ((test_id = dojo_test.id) AND (active = true))
                          Index Searches: 8
                          Buffers: shared hit=16 read=32
Planning:
  Buffers: shared hit=3 read=5
Planning Time: 0.396 ms
Execution Time: 57.761 ms
### products_sparse: dojo_product / 204c01f9, observed 1.01 ms
SELECT <projection> FROM "dojo_product" LEFT OUTER JOIN "dojo_product_platform" ON ("dojo_product"."platform_id" = "dojo_product_platform"."id") LEFT OUTER JOIN "dojo_product_lifecycle" ON ("dojo_product"."lifecycle_id" = "dojo_product_lifecycle"."id") LEFT OUTER JOIN "dojo_product_origin" ON ("dojo_product"."origin_id" = "dojo_product_origin"."id") WHERE "dojo_product"."id" IN (%s) ORDER BY "dojo_product"."name" ASC LIMIT 1
Limit  (cost=11.48..11.59 rows=1 width=3467) (actual rows=1.00 loops=1)
  Buffers: shared read=5
  ->  Unique  (cost=11.48..11.59 rows=1 width=3467) (actual rows=1.00 loops=1)
        Buffers: shared read=5
        ->  Sort  (cost=11.48..11.49 rows=1 width=3467) (actual rows=1.00 loops=1)
              Sort Key: dojo_product.name, dojo_product.created, dojo_product.updated, dojo_product.description, dojo_product.product_manager_id, dojo_product.technical_contact_id, dojo_product.team_manager_id, dojo_product.prod_type_id, dojo_product.sla_configuration_id, dojo_product.tid, dojo_product.prod_numeric_grade, dojo_product.business_criticality, dojo_product.platform_id, dojo_product.lifecycle_id, dojo_product.origin_id, dojo_product.user_records, dojo_product.revenue, dojo_product.external_audience, dojo_product.internet_accessible, dojo_product.enable_product_tag_inheritance, dojo_product.enable_simple_risk_acceptance, dojo_product.enable_full_risk_acceptance, dojo_product.disable_sla_breach_notifications, dojo_product.async_updating, dojo_product.archived_at, dojo_product.archive_batch, dojo_product_platform.id, dojo_product_platform.value, dojo_product_platform.name, dojo_product_platform.icon, dojo_product_platform.display_order, dojo_product_lifecycle.id, dojo_product_lifecycle.value, dojo_product_lifecycle.name, dojo_product_lifecycle.icon, dojo_product_lifecycle.display_order, dojo_product_origin.id, dojo_product_origin.value, dojo_product_origin.name, dojo_product_origin.icon, dojo_product_origin.display_order
              Sort Method: quicksort  Memory: 25kB
              Buffers: shared read=5
              ->  Nested Loop Left Join  (cost=0.14..11.47 rows=1 width=3467) (actual rows=1.00 loops=1)
                    Join Filter: (dojo_product.origin_id = dojo_product_origin.id)
                    Rows Removed by Join Filter: 6
                    Buffers: shared read=5
                    ->  Nested Loop Left Join  (cost=0.14..10.34 rows=1 width=2705) (actual rows=1.00 loops=1)
                          Join Filter: (dojo_product.lifecycle_id = dojo_product_lifecycle.id)
                          Rows Removed by Join Filter: 3
                          Buffers: shared read=4
                          ->  Nested Loop Left Join  (cost=0.14..9.27 rows=1 width=1943) (actual rows=1.00 loops=1)
                                Join Filter: (dojo_product.platform_id = dojo_product_platform.id)
                                Rows Removed by Join Filter: 5
                                Buffers: shared read=3
                                ->  Index Scan using dojo_product_pkey on dojo_product  (cost=0.14..8.16 rows=1 width=1181) (actual rows=1.00 loops=1)
                                      Index Cond: (id = 13)
                                      Index Searches: 1
                                      Buffers: shared read=2
                                ->  Seq Scan on dojo_product_platform  (cost=0.00..1.05 rows=5 width=762) (actual rows=5.00 loops=1)
                                      Buffers: shared read=1
                          ->  Seq Scan on dojo_product_lifecycle  (cost=0.00..1.03 rows=3 width=762) (actual rows=3.00 loops=1)
                                Buffers: shared read=1
                    ->  Seq Scan on dojo_product_origin  (cost=0.00..1.06 rows=6 width=762) (actual rows=6.00 loops=1)
                          Buffers: shared read=1
Planning:
  Buffers: shared read=1
Planning Time: 0.585 ms
Execution Time: 0.239 ms
{"case": "products_111k", "url": "/api/v2/products/?id=3,4,5,6&limit=4", "status": 200, "sql_count": 10, "sql_ms": 571.651, "fetch_ms": 0, "django_ms": 589.8, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_product / c088c0be": 1, "dojo_product / d3840c96": 1, "dojo_tagulous_product_tags / e0c4fbde": 1, "dojo_dojometa / 9b0eae3f": 1, "auth_user / be3aa76b": 1, "dojo_regulation / 376ff600": 1, "dojo_finding / 294fc18f": 1}, "bytes": 769460, "rows": 4}
### products_111k: dojo_finding / 294fc18f, observed 568.57 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_finding"."active" AND "dojo_engagement"."product_id" IN (%s, %s, %s, %s)) GROUP BY 1
GroupAggregate  (cost=175396.68..177908.62 rows=4 width=36) (actual rows=4.00 loops=1)
  Group Key: dojo_engagement.product_id
  Buffers: shared hit=16080 read=109114, temp read=246 written=247
  ->  Sort  (cost=175396.68..176233.98 rows=334918 width=8) (actual rows=111254.00 loops=1)
        Sort Key: dojo_engagement.product_id, dojo_finding.id
        Sort Method: external merge  Disk: 1968kB
        Buffers: shared hit=16080 read=109114, temp read=246 written=247
        ->  Hash Join  (cost=14.36..140080.68 rows=334918 width=8) (actual rows=111254.00 loops=1)
              Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
              Buffers: shared hit=16080 read=109114
              ->  Hash Join  (cost=4.16..137484.46 rows=837295 width=8) (actual rows=840282.00 loops=1)
                    Hash Cond: (dojo_finding.test_id = dojo_test.id)
                    Buffers: shared hit=16079 read=109114
                    ->  Seq Scan on dojo_finding  (cost=0.00..135185.37 rows=837295 width=8) (actual rows=840282.00 loops=1)
                          Filter: active
                          Rows Removed by Filter: 159718
                          Buffers: shared hit=16077 read=109114
                    ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                          Buckets: 1024  Batches: 1  Memory Usage: 12kB
                          Buffers: shared hit=2
                          ->  Seq Scan on dojo_test  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                                Buffers: shared hit=2
              ->  Hash  (cost=10.15..10.15 rows=4 width=8) (actual rows=8.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 9kB
                    Buffers: shared hit=1
                    ->  Seq Scan on dojo_engagement  (cost=0.00..10.15 rows=4 width=8) (actual rows=8.00 loops=1)
                          Filter: (product_id = ANY ('?'::integer[]))
                          Rows Removed by Filter: 16
                          Buffers: shared hit=1
Planning:
  Buffers: shared hit=8
Planning Time: 0.400 ms
JIT:
  Functions: 28
  Options: Inlining false, Optimization false, Expressions true, Deforming true
Execution Time: 566.017 ms
### products_111k: dojo_product / d3840c96, observed 1.02 ms
SELECT <projection> FROM "dojo_product" LEFT OUTER JOIN "dojo_product_platform" ON ("dojo_product"."platform_id" = "dojo_product_platform"."id") LEFT OUTER JOIN "dojo_product_lifecycle" ON ("dojo_product"."lifecycle_id" = "dojo_product_lifecycle"."id") LEFT OUTER JOIN "dojo_product_origin" ON ("dojo_product"."origin_id" = "dojo_product_origin"."id") WHERE "dojo_product"."id" IN (%s, %s, %s, %s) ORDER BY "dojo_product"."name" ASC LIMIT 4
Limit  (cost=14.29..14.72 rows=4 width=3467) (actual rows=4.00 loops=1)
  Buffers: shared hit=4
  ->  Unique  (cost=14.29..14.72 rows=4 width=3467) (actual rows=4.00 loops=1)
        Buffers: shared hit=4
        ->  Sort  (cost=14.29..14.30 rows=4 width=3467) (actual rows=4.00 loops=1)
              Sort Key: dojo_product.name, dojo_product.id, dojo_product.created, dojo_product.updated, dojo_product.description, dojo_product.product_manager_id, dojo_product.technical_contact_id, dojo_product.team_manager_id, dojo_product.prod_type_id, dojo_product.sla_configuration_id, dojo_product.tid, dojo_product.prod_numeric_grade, dojo_product.business_criticality, dojo_product.platform_id, dojo_product.lifecycle_id, dojo_product.origin_id, dojo_product.user_records, dojo_product.revenue, dojo_product.external_audience, dojo_product.internet_accessible, dojo_product.enable_product_tag_inheritance, dojo_product.enable_simple_risk_acceptance, dojo_product.enable_full_risk_acceptance, dojo_product.disable_sla_breach_notifications, dojo_product.async_updating, dojo_product.archived_at, dojo_product.archive_batch, dojo_product_platform.id, dojo_product_platform.value, dojo_product_platform.name, dojo_product_platform.icon, dojo_product_platform.display_order, dojo_product_lifecycle.id, dojo_product_lifecycle.value, dojo_product_lifecycle.name, dojo_product_lifecycle.icon, dojo_product_lifecycle.display_order, dojo_product_origin.id, dojo_product_origin.value, dojo_product_origin.name, dojo_product_origin.icon, dojo_product_origin.display_order
              Sort Method: quicksort  Memory: 25kB
              Buffers: shared hit=4
              ->  Hash Left Join  (cost=3.32..14.25 rows=4 width=3467) (actual rows=4.00 loops=1)
                    Hash Cond: (dojo_product.platform_id = dojo_product_platform.id)
                    Buffers: shared hit=4
                    ->  Hash Left Join  (cost=2.20..13.12 rows=4 width=2705) (actual rows=4.00 loops=1)
                          Hash Cond: (dojo_product.origin_id = dojo_product_origin.id)
                          Buffers: shared hit=3
                          ->  Hash Left Join  (cost=1.07..11.98 rows=4 width=1943) (actual rows=4.00 loops=1)
                                Hash Cond: (dojo_product.lifecycle_id = dojo_product_lifecycle.id)
                                Buffers: shared hit=2
                                ->  Seq Scan on dojo_product  (cost=0.00..10.90 rows=4 width=1181) (actual rows=4.00 loops=1)
                                      Filter: (id = ANY ('?'::integer[]))
                                      Rows Removed by Filter: 9
                                      Buffers: shared hit=1
                                ->  Hash  (cost=1.03..1.03 rows=3 width=762) (actual rows=3.00 loops=1)
                                      Buckets: 1024  Batches: 1  Memory Usage: 9kB
                                      Buffers: shared hit=1
                                      ->  Seq Scan on dojo_product_lifecycle  (cost=0.00..1.03 rows=3 width=762) (actual rows=3.00 loops=1)
                                            Buffers: shared hit=1
                          ->  Hash  (cost=1.06..1.06 rows=6 width=762) (actual rows=6.00 loops=1)
                                Buckets: 1024  Batches: 1  Memory Usage: 9kB
                                Buffers: shared hit=1
                                ->  Seq Scan on dojo_product_origin  (cost=0.00..1.06 rows=6 width=762) (actual rows=6.00 loops=1)
                                      Buffers: shared hit=1
                    ->  Hash  (cost=1.05..1.05 rows=5 width=762) (actual rows=5.00 loops=1)
                          Buckets: 1024  Batches: 1  Memory Usage: 9kB
                          Buffers: shared hit=1
                          ->  Seq Scan on dojo_product_platform  (cost=0.00..1.05 rows=5 width=762) (actual rows=5.00 loops=1)
                                Buffers: shared hit=1
Planning:
  Buffers: shared hit=1
Planning Time: 0.688 ms
Execution Time: 0.143 ms
{"case": "products_533k", "url": "/api/v2/products/?id=2&limit=1", "status": 200, "sql_count": 10, "sql_ms": 888.016, "fetch_ms": 0, "django_ms": 943.157, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_product / 2a592d23": 1, "dojo_product / 204c01f9": 1, "dojo_tagulous_product_tags / 07e72a97": 1, "dojo_dojometa / bf20f5e0": 1, "auth_user / 41271aed": 1, "dojo_regulation / 70ae594e": 1, "dojo_finding / 24240be4": 1}, "bytes": 3669627, "rows": 1}
### products_533k: dojo_finding / 24240be4, observed 884.27 ms
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
Planning Time: 0.550 ms
Execution Time: 943.795 ms
### products_533k: dojo_product / 204c01f9, observed 1.01 ms
SELECT <projection> FROM "dojo_product" LEFT OUTER JOIN "dojo_product_platform" ON ("dojo_product"."platform_id" = "dojo_product_platform"."id") LEFT OUTER JOIN "dojo_product_lifecycle" ON ("dojo_product"."lifecycle_id" = "dojo_product_lifecycle"."id") LEFT OUTER JOIN "dojo_product_origin" ON ("dojo_product"."origin_id" = "dojo_product_origin"."id") WHERE "dojo_product"."id" IN (%s) ORDER BY "dojo_product"."name" ASC LIMIT 1
Limit  (cost=11.48..11.59 rows=1 width=3467) (actual rows=1.00 loops=1)
  Buffers: shared read=5
  ->  Unique  (cost=11.48..11.59 rows=1 width=3467) (actual rows=1.00 loops=1)
        Buffers: shared read=5
        ->  Sort  (cost=11.48..11.49 rows=1 width=3467) (actual rows=1.00 loops=1)
              Sort Key: dojo_product.name, dojo_product.created, dojo_product.updated, dojo_product.description, dojo_product.product_manager_id, dojo_product.technical_contact_id, dojo_product.team_manager_id, dojo_product.prod_type_id, dojo_product.sla_configuration_id, dojo_product.tid, dojo_product.prod_numeric_grade, dojo_product.business_criticality, dojo_product.platform_id, dojo_product.lifecycle_id, dojo_product.origin_id, dojo_product.user_records, dojo_product.revenue, dojo_product.external_audience, dojo_product.internet_accessible, dojo_product.enable_product_tag_inheritance, dojo_product.enable_simple_risk_acceptance, dojo_product.enable_full_risk_acceptance, dojo_product.disable_sla_breach_notifications, dojo_product.async_updating, dojo_product.archived_at, dojo_product.archive_batch, dojo_product_platform.id, dojo_product_platform.value, dojo_product_platform.name, dojo_product_platform.icon, dojo_product_platform.display_order, dojo_product_lifecycle.id, dojo_product_lifecycle.value, dojo_product_lifecycle.name, dojo_product_lifecycle.icon, dojo_product_lifecycle.display_order, dojo_product_origin.id, dojo_product_origin.value, dojo_product_origin.name, dojo_product_origin.icon, dojo_product_origin.display_order
              Sort Method: quicksort  Memory: 25kB
              Buffers: shared read=5
              ->  Nested Loop Left Join  (cost=0.14..11.47 rows=1 width=3467) (actual rows=1.00 loops=1)
                    Join Filter: (dojo_product.origin_id = dojo_product_origin.id)
                    Rows Removed by Join Filter: 6
                    Buffers: shared read=5
                    ->  Nested Loop Left Join  (cost=0.14..10.34 rows=1 width=2705) (actual rows=1.00 loops=1)
                          Join Filter: (dojo_product.lifecycle_id = dojo_product_lifecycle.id)
                          Rows Removed by Join Filter: 3
                          Buffers: shared read=4
                          ->  Nested Loop Left Join  (cost=0.14..9.27 rows=1 width=1943) (actual rows=1.00 loops=1)
                                Join Filter: (dojo_product.platform_id = dojo_product_platform.id)
                                Rows Removed by Join Filter: 5
                                Buffers: shared read=3
                                ->  Index Scan using dojo_product_pkey on dojo_product  (cost=0.14..8.16 rows=1 width=1181) (actual rows=1.00 loops=1)
                                      Index Cond: (id = 2)
                                      Index Searches: 1
                                      Buffers: shared read=2
                                ->  Seq Scan on dojo_product_platform  (cost=0.00..1.05 rows=5 width=762) (actual rows=5.00 loops=1)
                                      Buffers: shared read=1
                          ->  Seq Scan on dojo_product_lifecycle  (cost=0.00..1.03 rows=3 width=762) (actual rows=3.00 loops=1)
                                Buffers: shared read=1
                    ->  Seq Scan on dojo_product_origin  (cost=0.00..1.06 rows=6 width=762) (actual rows=6.00 loops=1)
                          Buffers: shared read=1
Planning:
  Buffers: shared read=1
Planning Time: 0.587 ms
Execution Time: 0.303 ms
### products_533k: dojo_product / 2a592d23, observed 0.42 ms
SELECT <projection> FROM (SELECT DISTINCT "dojo_product"."id" AS "col1", "dojo_product"."created" AS "col2", "dojo_product"."updated" AS "col3", "dojo_product"."name" AS "col4", "dojo_product"."description" AS "col5", "dojo_product"."product_manager_id" AS "col6", "dojo_product"."technical_contact_id" AS "col7", "dojo_product"."team_manager_id" AS "col8", "dojo_product"."prod_type_id" AS "col9", "dojo_product"."sla_configuration_id" AS "col10", "dojo_product"."tid" AS "col11", "dojo_product"."prod_numeric_grade" AS "col12", "dojo_product"."business_criticality" AS "col13", "dojo_product"."platform_id" AS "col14", "dojo_product"."lifecycle_id" AS "col15", "dojo_product"."origin_id" AS "col16", "dojo_product"."user_records" AS "col17", "dojo_product"."revenue" AS "col18", "dojo_product"."external_audience" AS "col19", "dojo_product"."internet_accessible" AS "col20", "dojo_product"."enable_product_tag_inheritance" AS "col21", "dojo_product"."enable_simple_risk_acceptance" AS "col22", "dojo_product"."enable_full_risk_acceptance" AS "col23", "dojo_product"."disable_sla_breach_notifications" AS "col24", "dojo_product"."async_updating" AS "col25", "dojo_product"."archived_at" AS "col26", "dojo_product"."archive_batch" AS "col27" FROM "dojo_product" WHERE "dojo_product"."id" IN (%s)) subquery
Aggregate  (cost=8.25..8.26 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=2
  ->  Unique  (cost=8.17..8.24 rows=1 width=1181) (actual rows=1.00 loops=1)
        Buffers: shared hit=2
        ->  Sort  (cost=8.17..8.17 rows=1 width=1181) (actual rows=1.00 loops=1)
              Sort Key: dojo_product.created, dojo_product.updated, dojo_product.name, dojo_product.description, dojo_product.product_manager_id, dojo_product.technical_contact_id, dojo_product.team_manager_id, dojo_product.prod_type_id, dojo_product.sla_configuration_id, dojo_product.tid, dojo_product.prod_numeric_grade, dojo_product.business_criticality, dojo_product.platform_id, dojo_product.lifecycle_id, dojo_product.origin_id, dojo_product.user_records, dojo_product.revenue, dojo_product.external_audience, dojo_product.internet_accessible, dojo_product.enable_product_tag_inheritance, dojo_product.enable_simple_risk_acceptance, dojo_product.enable_full_risk_acceptance, dojo_product.disable_sla_breach_notifications, dojo_product.async_updating, dojo_product.archived_at, dojo_product.archive_batch
              Sort Method: quicksort  Memory: 25kB
              Buffers: shared hit=2
              ->  Index Scan using dojo_product_pkey on dojo_product  (cost=0.14..8.16 rows=1 width=1181) (actual rows=1.00 loops=1)
                    Index Cond: (id = 2)
                    Index Searches: 1
                    Buffers: shared hit=2
Planning:
  Buffers: shared hit=1
Planning Time: 0.138 ms
Execution Time: 0.058 ms
{"case": "products_840k", "url": "/api/v2/products/?limit=100", "status": 200, "sql_count": 10, "sql_ms": 871.99, "fetch_ms": 0, "django_ms": 971.365, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_product / 888bac19": 1, "dojo_product / d348b756": 1, "dojo_tagulous_product_tags / 0d949bb1": 1, "dojo_dojometa / b9c3a816": 1, "auth_user / 00777406": 1, "dojo_regulation / d339dab0": 1, "dojo_finding / 0a7c0e0e": 1}, "bytes": 5798301, "rows": 13}
### products_840k: dojo_finding / 0a7c0e0e, observed 868.04 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_finding"."active" AND "dojo_engagement"."product_id" IN (<parameters>)) GROUP BY 1
GroupAggregate  (cost=204247.05..208642.94 rows=7 width=36) (actual rows=12.00 loops=1)
  Group Key: dojo_engagement.product_id
  Buffers: shared hit=16243 read=108951, temp read=1859 written=1869
  ->  Sort  (cost=204247.05..205712.32 rows=586106 width=8) (actual rows=840282.00 loops=1)
        Sort Key: dojo_engagement.product_id, dojo_finding.id
        Sort Method: external merge  Disk: 14872kB
        Buffers: shared hit=16243 read=108951, temp read=1859 written=1869
        ->  Hash Join  (cost=14.43..140080.75 rows=586106 width=8) (actual rows=840282.00 loops=1)
              Hash Cond: (dojo_test.engagement_id = dojo_engagement.id)
              Buffers: shared hit=16243 read=108951
              ->  Hash Join  (cost=4.16..137484.46 rows=837295 width=8) (actual rows=840282.00 loops=1)
                    Hash Cond: (dojo_finding.test_id = dojo_test.id)
                    Buffers: shared hit=16242 read=108951
                    ->  Seq Scan on dojo_finding  (cost=0.00..135185.37 rows=837295 width=8) (actual rows=840282.00 loops=1)
                          Filter: active
                          Rows Removed by Filter: 159718
                          Buffers: shared hit=16240 read=108951
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
Planning Time: 0.863 ms
JIT:
  Functions: 28
  Options: Inlining false, Optimization false, Expressions true, Deforming true
Execution Time: 945.353 ms
### products_840k: dojo_product / d348b756, observed 1.23 ms
SELECT <projection> FROM "dojo_product" LEFT OUTER JOIN "dojo_product_platform" ON ("dojo_product"."platform_id" = "dojo_product_platform"."id") LEFT OUTER JOIN "dojo_product_lifecycle" ON ("dojo_product"."lifecycle_id" = "dojo_product_lifecycle"."id") LEFT OUTER JOIN "dojo_product_origin" ON ("dojo_product"."origin_id" = "dojo_product_origin"."id") ORDER BY "dojo_product"."name" ASC LIMIT 100
Limit  (cost=16.19..22.64 rows=60 width=3467) (actual rows=13.00 loops=1)
  Buffers: shared hit=4
  ->  Unique  (cost=16.19..22.64 rows=60 width=3467) (actual rows=13.00 loops=1)
        Buffers: shared hit=4
        ->  Sort  (cost=16.19..16.34 rows=60 width=3467) (actual rows=13.00 loops=1)
              Sort Key: dojo_product.name, dojo_product.id, dojo_product.created, dojo_product.updated, dojo_product.description, dojo_product.product_manager_id, dojo_product.technical_contact_id, dojo_product.team_manager_id, dojo_product.prod_type_id, dojo_product.sla_configuration_id, dojo_product.tid, dojo_product.prod_numeric_grade, dojo_product.business_criticality, dojo_product.platform_id, dojo_product.lifecycle_id, dojo_product.origin_id, dojo_product.user_records, dojo_product.revenue, dojo_product.external_audience, dojo_product.internet_accessible, dojo_product.enable_product_tag_inheritance, dojo_product.enable_simple_risk_acceptance, dojo_product.enable_full_risk_acceptance, dojo_product.disable_sla_breach_notifications, dojo_product.async_updating, dojo_product.archived_at, dojo_product.archive_batch, dojo_product_platform.id, dojo_product_platform.value, dojo_product_platform.name, dojo_product_platform.icon, dojo_product_platform.display_order, dojo_product_lifecycle.id, dojo_product_lifecycle.value, dojo_product_lifecycle.name, dojo_product_lifecycle.icon, dojo_product_lifecycle.display_order, dojo_product_origin.id, dojo_product_origin.value, dojo_product_origin.name, dojo_product_origin.icon, dojo_product_origin.display_order
              Sort Method: quicksort  Memory: 26kB
              Buffers: shared hit=4
              ->  Hash Left Join  (cost=3.32..14.42 rows=60 width=3467) (actual rows=13.00 loops=1)
                    Hash Cond: (dojo_product.origin_id = dojo_product_origin.id)
                    Buffers: shared hit=4
                    ->  Hash Left Join  (cost=2.18..13.12 rows=60 width=2705) (actual rows=13.00 loops=1)
                          Hash Cond: (dojo_product.lifecycle_id = dojo_product_lifecycle.id)
                          Buffers: shared hit=3
                          ->  Hash Left Join  (cost=1.11..11.88 rows=60 width=1943) (actual rows=13.00 loops=1)
                                Hash Cond: (dojo_product.platform_id = dojo_product_platform.id)
                                Buffers: shared hit=2
                                ->  Seq Scan on dojo_product  (cost=0.00..10.60 rows=60 width=1181) (actual rows=13.00 loops=1)
                                      Buffers: shared hit=1
                                ->  Hash  (cost=1.05..1.05 rows=5 width=762) (actual rows=5.00 loops=1)
                                      Buckets: 1024  Batches: 1  Memory Usage: 9kB
                                      Buffers: shared hit=1
                                      ->  Seq Scan on dojo_product_platform  (cost=0.00..1.05 rows=5 width=762) (actual rows=5.00 loops=1)
                                            Buffers: shared hit=1
                          ->  Hash  (cost=1.03..1.03 rows=3 width=762) (actual rows=3.00 loops=1)
                                Buckets: 1024  Batches: 1  Memory Usage: 9kB
                                Buffers: shared hit=1
                                ->  Seq Scan on dojo_product_lifecycle  (cost=0.00..1.03 rows=3 width=762) (actual rows=3.00 loops=1)
                                      Buffers: shared hit=1
                    ->  Hash  (cost=1.06..1.06 rows=6 width=762) (actual rows=6.00 loops=1)
                          Buckets: 1024  Batches: 1  Memory Usage: 9kB
                          Buffers: shared hit=1
                          ->  Seq Scan on dojo_product_origin  (cost=0.00..1.06 rows=6 width=762) (actual rows=6.00 loops=1)
                                Buffers: shared hit=1
Planning:
  Buffers: shared hit=1
Planning Time: 0.757 ms
Execution Time: 0.204 ms
### products_840k: dojo_product / 888bac19, observed 0.58 ms
SELECT <projection> FROM (SELECT DISTINCT "dojo_product"."id" AS "col1", "dojo_product"."created" AS "col2", "dojo_product"."updated" AS "col3", "dojo_product"."name" AS "col4", "dojo_product"."description" AS "col5", "dojo_product"."product_manager_id" AS "col6", "dojo_product"."technical_contact_id" AS "col7", "dojo_product"."team_manager_id" AS "col8", "dojo_product"."prod_type_id" AS "col9", "dojo_product"."sla_configuration_id" AS "col10", "dojo_product"."tid" AS "col11", "dojo_product"."prod_numeric_grade" AS "col12", "dojo_product"."business_criticality" AS "col13", "dojo_product"."platform_id" AS "col14", "dojo_product"."lifecycle_id" AS "col15", "dojo_product"."origin_id" AS "col16", "dojo_product"."user_records" AS "col17", "dojo_product"."revenue" AS "col18", "dojo_product"."external_audience" AS "col19", "dojo_product"."internet_accessible" AS "col20", "dojo_product"."enable_product_tag_inheritance" AS "col21", "dojo_product"."enable_simple_risk_acceptance" AS "col22", "dojo_product"."enable_full_risk_acceptance" AS "col23", "dojo_product"."disable_sla_breach_notifications" AS "col24", "dojo_product"."async_updating" AS "col25", "dojo_product"."archived_at" AS "col26", "dojo_product"."archive_batch" AS "col27" FROM "dojo_product") subquery
Aggregate  (cost=16.00..16.01 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=1
  ->  HashAggregate  (cost=14.65..15.25 rows=60 width=1181) (actual rows=13.00 loops=1)
        Group Key: dojo_product.id, dojo_product.created, dojo_product.updated, dojo_product.name, dojo_product.description, dojo_product.product_manager_id, dojo_product.technical_contact_id, dojo_product.team_manager_id, dojo_product.prod_type_id, dojo_product.sla_configuration_id, dojo_product.tid, dojo_product.prod_numeric_grade, dojo_product.business_criticality, dojo_product.platform_id, dojo_product.lifecycle_id, dojo_product.origin_id, dojo_product.user_records, dojo_product.revenue, dojo_product.external_audience, dojo_product.internet_accessible, dojo_product.enable_product_tag_inheritance, dojo_product.enable_simple_risk_acceptance, dojo_product.enable_full_risk_acceptance, dojo_product.disable_sla_breach_notifications, dojo_product.async_updating, dojo_product.archived_at, dojo_product.archive_batch
        Batches: 1  Memory Usage: 88kB
        Buffers: shared hit=1
        ->  Seq Scan on dojo_product  (cost=0.00..10.60 rows=60 width=1181) (actual rows=13.00 loops=1)
              Buffers: shared hit=1
Planning:
  Buffers: shared hit=1
Planning Time: 0.096 ms
Execution Time: 0.063 ms
{"case": "engagements_1", "url": "/api/v2/engagements/?limit=1", "status": 200, "sql_count": 9, "sql_ms": 2.502, "fetch_ms": 0, "django_ms": 11.019, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_engagement / 19d36082": 1, "dojo_engagement / db0e3f4e": 1, "dojo_notes / c8142c5a": 1, "dojo_risk_acceptance / eb993df3": 1, "dojo_fileupload / 396fcebb": 1, "dojo_tagulous_engagement_tags / 55e9f977": 1}, "bytes": 964, "rows": 1}
### engagements_1: dojo_notes / c8142c5a, observed 0.52 ms
SELECT <projection> FROM "dojo_notes" INNER JOIN "dojo_engagement_notes" ON ("dojo_notes"."id" = "dojo_engagement_notes"."notes_id") LEFT OUTER JOIN "dojo_note_type" ON ("dojo_notes"."note_type_id" = "dojo_note_type"."id") INNER JOIN "auth_user" ON ("dojo_notes"."author_id" = "auth_user"."id") LEFT OUTER JOIN "auth_user" T6 ON ("dojo_notes"."editor_id" = T6."id") WHERE "dojo_engagement_notes"."engagement_id" IN (%s) ORDER BY "dojo_notes"."date" DESC
Sort  (cost=42.33..42.36 rows=10 width=4247) (actual rows=0.00 loops=1)
  Sort Key: dojo_notes.date DESC
  Sort Method: quicksort  Memory: 25kB
  ->  Nested Loop Left Join  (cost=15.33..42.16 rows=10 width=4247) (actual rows=0.00 loops=1)
        ->  Nested Loop  (cost=15.19..40.03 rows=10 width=2480) (actual rows=0.00 loops=1)
              ->  Nested Loop Left Join  (cost=15.05..37.89 rows=10 width=713) (actual rows=0.00 loops=1)
                    ->  Hash Join  (cost=14.91..35.78 rows=10 width=70) (actual rows=0.00 loops=1)
                          Hash Cond: (dojo_notes.id = dojo_engagement_notes.notes_id)
                          ->  Seq Scan on dojo_notes  (cost=0.00..18.60 rows=860 width=66) (actual rows=0.00 loops=1)
                          ->  Hash  (cost=14.79..14.79 rows=10 width=8) (never executed)
                                ->  Bitmap Heap Scan on dojo_engagement_notes  (cost=4.23..14.79 rows=10 width=8) (never executed)
                                      Recheck Cond: (engagement_id = 1)
                                      ->  Bitmap Index Scan on dojo_engagement_notes_engagement_id_6d165427  (cost=0.00..4.23 rows=10 width=0) (never executed)
                                            Index Cond: (engagement_id = 1)
                                            Index Searches: 0
                    ->  Index Scan using dojo_note_type_pkey on dojo_note_type  (cost=0.14..0.21 rows=1 width=643) (never executed)
                          Index Cond: (id = dojo_notes.note_type_id)
                          Index Searches: 0
              ->  Index Scan using auth_user_pkey on auth_user  (cost=0.14..0.21 rows=1 width=1767) (never executed)
                    Index Cond: (id = dojo_notes.author_id)
                    Index Searches: 0
        ->  Index Scan using auth_user_pkey on auth_user t6  (cost=0.14..0.21 rows=1 width=1767) (never executed)
              Index Cond: (id = dojo_notes.editor_id)
              Index Searches: 0
Planning:
  Buffers: shared hit=11
Planning Time: 0.249 ms
Execution Time: 0.046 ms
{"case": "engagements_20", "url": "/api/v2/engagements/?limit=20", "status": 200, "sql_count": 9, "sql_ms": 2.627, "fetch_ms": 0, "django_ms": 58.653, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_engagement / 19d36082": 1, "dojo_engagement / 00cabe53": 1, "dojo_notes / 3da31464": 1, "dojo_risk_acceptance / e11b6d2a": 1, "dojo_fileupload / 12cce93d": 1, "dojo_tagulous_engagement_tags / fdc485d6": 1}, "bytes": 17340, "rows": 20}
### engagements_20: dojo_tagulous_engagement_tags / fdc485d6, observed 0.49 ms
SELECT <projection> FROM "dojo_tagulous_engagement_tags" INNER JOIN "dojo_engagement_tags" ON ("dojo_tagulous_engagement_tags"."id" = "dojo_engagement_tags"."tagulous_engagement_tags_id") WHERE "dojo_engagement_tags"."engagement_id" IN (<parameters>) ORDER BY "dojo_tagulous_engagement_tags"."name" ASC
Sort  (cost=39.92..40.43 rows=204 width=647) (actual rows=0.00 loops=1)
  Sort Key: dojo_tagulous_engagement_tags.name
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=2
  ->  Hash Join  (cost=18.48..32.09 rows=204 width=647) (actual rows=0.00 loops=1)
        Hash Cond: (dojo_engagement_tags.tagulous_engagement_tags_id = dojo_tagulous_engagement_tags.id)
        Buffers: shared hit=2
        ->  Bitmap Heap Scan on dojo_engagement_tags  (cost=5.78..18.84 rows=204 width=8) (actual rows=0.00 loops=1)
              Recheck Cond: (engagement_id = ANY ('?'::integer[]))
              Buffers: shared hit=2
              ->  Bitmap Index Scan on dojo_engagement_tags_engagement_id_754fed5e  (cost=0.00..5.68 rows=204 width=0) (actual rows=0.00 loops=1)
                    Index Cond: (engagement_id = ANY ('?'::integer[]))
                    Index Searches: 1
                    Buffers: shared hit=2
        ->  Hash  (cost=11.20..11.20 rows=120 width=643) (never executed)
              ->  Seq Scan on dojo_tagulous_engagement_tags  (cost=0.00..11.20 rows=120 width=643) (never executed)
Planning:
  Buffers: shared hit=10
Planning Time: 0.080 ms
Execution Time: 0.028 ms
### engagements_20: dojo_notes / 3da31464, observed 0.48 ms
SELECT <projection> FROM "dojo_notes" INNER JOIN "dojo_engagement_notes" ON ("dojo_notes"."id" = "dojo_engagement_notes"."notes_id") LEFT OUTER JOIN "dojo_note_type" ON ("dojo_notes"."note_type_id" = "dojo_note_type"."id") INNER JOIN "auth_user" ON ("dojo_notes"."author_id" = "auth_user"."id") LEFT OUTER JOIN "auth_user" T6 ON ("dojo_notes"."editor_id" = T6."id") WHERE "dojo_engagement_notes"."engagement_id" IN (<parameters>) ORDER BY "dojo_notes"."date" DESC
Sort  (cost=92.69..93.20 rows=204 width=4247) (actual rows=0.00 loops=1)
  Sort Key: dojo_notes.date DESC
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=3
  ->  Hash Left Join  (cost=69.63..84.87 rows=204 width=4247) (actual rows=0.00 loops=1)
        Hash Cond: (dojo_notes.editor_id = t6.id)
        Buffers: shared hit=3
        ->  Hash Join  (cost=58.73..73.42 rows=204 width=2480) (actual rows=0.00 loops=1)
              Hash Cond: (dojo_notes.author_id = auth_user.id)
              Buffers: shared hit=3
              ->  Hash Left Join  (cost=47.83..61.98 rows=204 width=713) (actual rows=0.00 loops=1)
                    Hash Cond: (dojo_notes.note_type_id = dojo_note_type.id)
                    Buffers: shared hit=2
                    ->  Hash Join  (cost=35.13..48.73 rows=204 width=70) (actual rows=0.00 loops=1)
                          Hash Cond: (dojo_engagement_notes.notes_id = dojo_notes.id)
                          Buffers: shared hit=2
                          ->  Bitmap Heap Scan on dojo_engagement_notes  (cost=5.78..18.84 rows=204 width=8) (actual rows=0.00 loops=1)
                                Recheck Cond: (engagement_id = ANY ('?'::integer[]))
                                Buffers: shared hit=2
                                ->  Bitmap Index Scan on dojo_engagement_notes_engagement_id_6d165427  (cost=0.00..5.68 rows=204 width=0) (actual rows=0.00 loops=1)
                                      Index Cond: (engagement_id = ANY ('?'::integer[]))
                                      Index Searches: 1
                                      Buffers: shared hit=2
                          ->  Hash  (cost=18.60..18.60 rows=860 width=66) (never executed)
                                ->  Seq Scan on dojo_notes  (cost=0.00..18.60 rows=860 width=66) (never executed)
                    ->  Hash  (cost=11.20..11.20 rows=120 width=643) (never executed)
                          ->  Seq Scan on dojo_note_type  (cost=0.00..11.20 rows=120 width=643) (never executed)
              ->  Hash  (cost=10.40..10.40 rows=40 width=1767) (actual rows=1.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 9kB
                    Buffers: shared hit=1
                    ->  Seq Scan on auth_user  (cost=0.00..10.40 rows=40 width=1767) (actual rows=1.00 loops=1)
                          Buffers: shared hit=1
        ->  Hash  (cost=10.40..10.40 rows=40 width=1767) (never executed)
              ->  Seq Scan on auth_user t6  (cost=0.00..10.40 rows=40 width=1767) (never executed)
Planning:
  Buffers: shared hit=11
Planning Time: 0.281 ms
Execution Time: 0.093 ms
{"case": "engagements_100", "url": "/api/v2/engagements/?limit=100", "status": 200, "sql_count": 9, "sql_ms": 3.087, "fetch_ms": 0, "django_ms": 18.663, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_engagement / 19d36082": 1, "dojo_engagement / 35986069": 1, "dojo_notes / f7768e16": 1, "dojo_risk_acceptance / 11a7aa68": 1, "dojo_fileupload / edb4abb7": 1, "dojo_tagulous_engagement_tags / 4fd8464a": 1}, "bytes": 20739, "rows": 24}
### engagements_100: dojo_notes / f7768e16, observed 0.57 ms
SELECT <projection> FROM "dojo_notes" INNER JOIN "dojo_engagement_notes" ON ("dojo_notes"."id" = "dojo_engagement_notes"."notes_id") LEFT OUTER JOIN "dojo_note_type" ON ("dojo_notes"."note_type_id" = "dojo_note_type"."id") INNER JOIN "auth_user" ON ("dojo_notes"."author_id" = "auth_user"."id") LEFT OUTER JOIN "auth_user" T6 ON ("dojo_notes"."editor_id" = T6."id") WHERE "dojo_engagement_notes"."engagement_id" IN (<parameters>) ORDER BY "dojo_notes"."date" DESC
Sort  (cost=95.96..96.58 rows=245 width=4247) (actual rows=0.00 loops=1)
  Sort Key: dojo_notes.date DESC
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=3
  ->  Hash Left Join  (cost=69.96..86.24 rows=245 width=4247) (actual rows=0.00 loops=1)
        Hash Cond: (dojo_notes.editor_id = t6.id)
        Buffers: shared hit=3
        ->  Hash Join  (cost=59.06..74.69 rows=245 width=2480) (actual rows=0.00 loops=1)
              Hash Cond: (dojo_notes.author_id = auth_user.id)
              Buffers: shared hit=3
              ->  Hash Left Join  (cost=48.16..63.13 rows=245 width=713) (actual rows=0.00 loops=1)
                    Hash Cond: (dojo_notes.note_type_id = dojo_note_type.id)
                    Buffers: shared hit=2
                    ->  Hash Join  (cost=35.46..49.78 rows=245 width=70) (actual rows=0.00 loops=1)
                          Hash Cond: (dojo_engagement_notes.notes_id = dojo_notes.id)
                          Buffers: shared hit=2
                          ->  Bitmap Heap Scan on dojo_engagement_notes  (cost=6.11..19.79 rows=245 width=8) (actual rows=0.00 loops=1)
                                Recheck Cond: (engagement_id = ANY ('?'::integer[]))
                                Buffers: shared hit=2
                                ->  Bitmap Index Scan on dojo_engagement_notes_engagement_id_6d165427  (cost=0.00..5.99 rows=245 width=0) (actual rows=0.00 loops=1)
                                      Index Cond: (engagement_id = ANY ('?'::integer[]))
                                      Index Searches: 1
                                      Buffers: shared hit=2
                          ->  Hash  (cost=18.60..18.60 rows=860 width=66) (never executed)
                                ->  Seq Scan on dojo_notes  (cost=0.00..18.60 rows=860 width=66) (never executed)
                    ->  Hash  (cost=11.20..11.20 rows=120 width=643) (never executed)
                          ->  Seq Scan on dojo_note_type  (cost=0.00..11.20 rows=120 width=643) (never executed)
              ->  Hash  (cost=10.40..10.40 rows=40 width=1767) (actual rows=1.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 9kB
                    Buffers: shared hit=1
                    ->  Seq Scan on auth_user  (cost=0.00..10.40 rows=40 width=1767) (actual rows=1.00 loops=1)
                          Buffers: shared hit=1
        ->  Hash  (cost=10.40..10.40 rows=40 width=1767) (never executed)
              ->  Seq Scan on auth_user t6  (cost=0.00..10.40 rows=40 width=1767) (never executed)
Planning:
  Buffers: shared hit=11
Planning Time: 0.280 ms
Execution Time: 0.079 ms
### engagements_100: dojo_engagement / 19d36082, observed 0.42 ms
SELECT <projection> FROM (SELECT DISTINCT "dojo_engagement"."id" AS "col1", "dojo_engagement"."created" AS "col2", "dojo_engagement"."updated" AS "col3", "dojo_engagement"."name" AS "col4", "dojo_engagement"."description" AS "col5", "dojo_engagement"."version" AS "col6", "dojo_engagement"."first_contacted" AS "col7", "dojo_engagement"."target_start" AS "col8", "dojo_engagement"."target_end" AS "col9", "dojo_engagement"."lead_id" AS "col10", "dojo_engagement"."requester_id" AS "col11", "dojo_engagement"."preset_id" AS "col12", "dojo_engagement"."reason" AS "col13", "dojo_engagement"."report_type_id" AS "col14", "dojo_engagement"."product_id" AS "col15", "dojo_engagement"."active" AS "col16", "dojo_engagement"."tracker" AS "col17", "dojo_engagement"."test_strategy" AS "col18", "dojo_engagement"."threat_model" AS "col19", "dojo_engagement"."api_test" AS "col20", "dojo_engagement"."pen_test" AS "col21", "dojo_engagement"."check_list" AS "col22", "dojo_engagement"."status" AS "col23", "dojo_engagement"."progress" AS "col24", "dojo_engagement"."tmodel_path" AS "col25", "dojo_engagement"."done_testing" AS "col26", "dojo_engagement"."engagement_type" AS "col27", "dojo_engagement"."build_id" AS "col28", "dojo_engagement"."commit_hash" AS "col29", "dojo_engagement"."branch_tag" AS "col30", "dojo_engagement"."source_code_management_uri" AS "col31", "dojo_engagement"."cicd_scm_server_id" A
Aggregate  (cost=11.34..11.35 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=1
  ->  Unique  (cost=10.27..11.22 rows=10 width=5495) (actual rows=24.00 loops=1)
        Buffers: shared hit=1
        ->  Sort  (cost=10.27..10.29 rows=10 width=5495) (actual rows=24.00 loops=1)
              Sort Key: dojo_engagement.id, dojo_engagement.created, dojo_engagement.updated, dojo_engagement.name, dojo_engagement.description, dojo_engagement.version, dojo_engagement.first_contacted, dojo_engagement.target_start, dojo_engagement.target_end, dojo_engagement.lead_id, dojo_engagement.requester_id, dojo_engagement.preset_id, dojo_engagement.reason, dojo_engagement.report_type_id, dojo_engagement.product_id, dojo_engagement.active, dojo_engagement.tracker, dojo_engagement.test_strategy, dojo_engagement.threat_model, dojo_engagement.api_test, dojo_engagement.pen_test, dojo_engagement.check_list, dojo_engagement.status, dojo_engagement.progress, dojo_engagement.tmodel_path, dojo_engagement.done_testing, dojo_engagement.engagement_type, dojo_engagement.build_id, dojo_engagement.commit_hash, dojo_engagement.branch_tag, dojo_engagement.source_code_management_uri, dojo_engagement.cicd_scm_server_id, dojo_engagement.cicd_build_server_id, dojo_engagement.cicd_orchestration_engine_id, dojo_engagement.deduplication_on_engagement, dojo_engagement.archived_at, dojo_engagement.archive_batch
              Sort Method: quicksort  Memory: 28kB
              Buffers: shared hit=1
              ->  Seq Scan on dojo_engagement  (cost=0.00..10.10 rows=10 width=5495) (actual rows=24.00 loops=1)
                    Buffers: shared hit=1
Planning:
  Buffers: shared hit=1
Planning Time: 0.121 ms
Execution Time: 0.079 ms
{"case": "engagement_detail", "url": "/api/v2/engagements/1/", "status": 200, "sql_count": 8, "sql_ms": 2.136, "fetch_ms": 0, "django_ms": 10.889, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_engagement / 343b5f2b": 1, "dojo_notes / c8142c5a": 1, "dojo_risk_acceptance / eb993df3": 1, "dojo_fileupload / 396fcebb": 1, "dojo_tagulous_engagement_tags / 55e9f977": 1}, "bytes": 860, "rows": 1}
### engagement_detail: dojo_notes / c8142c5a, observed 0.47 ms
SELECT <projection> FROM "dojo_notes" INNER JOIN "dojo_engagement_notes" ON ("dojo_notes"."id" = "dojo_engagement_notes"."notes_id") LEFT OUTER JOIN "dojo_note_type" ON ("dojo_notes"."note_type_id" = "dojo_note_type"."id") INNER JOIN "auth_user" ON ("dojo_notes"."author_id" = "auth_user"."id") LEFT OUTER JOIN "auth_user" T6 ON ("dojo_notes"."editor_id" = T6."id") WHERE "dojo_engagement_notes"."engagement_id" IN (%s) ORDER BY "dojo_notes"."date" DESC
Sort  (cost=42.33..42.36 rows=10 width=4247) (actual rows=0.00 loops=1)
  Sort Key: dojo_notes.date DESC
  Sort Method: quicksort  Memory: 25kB
  ->  Nested Loop Left Join  (cost=15.33..42.16 rows=10 width=4247) (actual rows=0.00 loops=1)
        ->  Nested Loop  (cost=15.19..40.03 rows=10 width=2480) (actual rows=0.00 loops=1)
              ->  Nested Loop Left Join  (cost=15.05..37.89 rows=10 width=713) (actual rows=0.00 loops=1)
                    ->  Hash Join  (cost=14.91..35.78 rows=10 width=70) (actual rows=0.00 loops=1)
                          Hash Cond: (dojo_notes.id = dojo_engagement_notes.notes_id)
                          ->  Seq Scan on dojo_notes  (cost=0.00..18.60 rows=860 width=66) (actual rows=0.00 loops=1)
                          ->  Hash  (cost=14.79..14.79 rows=10 width=8) (never executed)
                                ->  Bitmap Heap Scan on dojo_engagement_notes  (cost=4.23..14.79 rows=10 width=8) (never executed)
                                      Recheck Cond: (engagement_id = 1)
                                      ->  Bitmap Index Scan on dojo_engagement_notes_engagement_id_6d165427  (cost=0.00..4.23 rows=10 width=0) (never executed)
                                            Index Cond: (engagement_id = 1)
                                            Index Searches: 0
                    ->  Index Scan using dojo_note_type_pkey on dojo_note_type  (cost=0.14..0.21 rows=1 width=643) (never executed)
                          Index Cond: (id = dojo_notes.note_type_id)
                          Index Searches: 0
              ->  Index Scan using auth_user_pkey on auth_user  (cost=0.14..0.21 rows=1 width=1767) (never executed)
                    Index Cond: (id = dojo_notes.author_id)
                    Index Searches: 0
        ->  Index Scan using auth_user_pkey on auth_user t6  (cost=0.14..0.21 rows=1 width=1767) (never executed)
              Index Cond: (id = dojo_notes.editor_id)
              Index Searches: 0
Planning:
  Buffers: shared hit=11
Planning Time: 0.255 ms
Execution Time: 0.051 ms
{"case": "tests_1", "url": "/api/v2/tests/?limit=1", "status": 200, "sql_count": 9, "sql_ms": 2.357, "fetch_ms": 0, "django_ms": 10.52, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_test / 34915665": 1, "dojo_test / 80f63d90": 1, "dojo_notes / 62704bb0": 1, "dojo_fileupload / 64b43434": 1, "dojo_tagulous_test_tags / 87c84f78": 1, "dojo_finding_group / 370c05b6": 1}, "bytes": 749, "rows": 1}
### tests_1: dojo_notes / 62704bb0, observed 0.49 ms
SELECT <projection> FROM "dojo_notes" INNER JOIN "dojo_test_notes" ON ("dojo_notes"."id" = "dojo_test_notes"."notes_id") LEFT OUTER JOIN "dojo_note_type" ON ("dojo_notes"."note_type_id" = "dojo_note_type"."id") INNER JOIN "auth_user" ON ("dojo_notes"."author_id" = "auth_user"."id") LEFT OUTER JOIN "auth_user" T6 ON ("dojo_notes"."editor_id" = T6."id") WHERE "dojo_test_notes"."test_id" IN (%s) ORDER BY "dojo_notes"."date" DESC
Sort  (cost=42.33..42.36 rows=10 width=4247) (actual rows=0.00 loops=1)
  Sort Key: dojo_notes.date DESC
  Sort Method: quicksort  Memory: 25kB
  ->  Nested Loop Left Join  (cost=15.33..42.16 rows=10 width=4247) (actual rows=0.00 loops=1)
        ->  Nested Loop  (cost=15.19..40.03 rows=10 width=2480) (actual rows=0.00 loops=1)
              ->  Nested Loop Left Join  (cost=15.05..37.89 rows=10 width=713) (actual rows=0.00 loops=1)
                    ->  Hash Join  (cost=14.91..35.78 rows=10 width=70) (actual rows=0.00 loops=1)
                          Hash Cond: (dojo_notes.id = dojo_test_notes.notes_id)
                          ->  Seq Scan on dojo_notes  (cost=0.00..18.60 rows=860 width=66) (actual rows=0.00 loops=1)
                          ->  Hash  (cost=14.79..14.79 rows=10 width=8) (never executed)
                                ->  Bitmap Heap Scan on dojo_test_notes  (cost=4.23..14.79 rows=10 width=8) (never executed)
                                      Recheck Cond: (test_id = 1)
                                      ->  Bitmap Index Scan on dojo_test_notes_test_id_16d6acce  (cost=0.00..4.23 rows=10 width=0) (never executed)
                                            Index Cond: (test_id = 1)
                                            Index Searches: 0
                    ->  Index Scan using dojo_note_type_pkey on dojo_note_type  (cost=0.14..0.21 rows=1 width=643) (never executed)
                          Index Cond: (id = dojo_notes.note_type_id)
                          Index Searches: 0
              ->  Index Scan using auth_user_pkey on auth_user  (cost=0.14..0.21 rows=1 width=1767) (never executed)
                    Index Cond: (id = dojo_notes.author_id)
                    Index Searches: 0
        ->  Index Scan using auth_user_pkey on auth_user t6  (cost=0.14..0.21 rows=1 width=1767) (never executed)
              Index Cond: (id = dojo_notes.editor_id)
              Index Searches: 0
Planning:
  Buffers: shared hit=11
Planning Time: 0.275 ms
Execution Time: 0.073 ms
### tests_1: dojo_test / 80f63d90, observed 0.48 ms
SELECT <projection> FROM "dojo_test" INNER JOIN "dojo_test_type" ON ("dojo_test"."test_type_id" = "dojo_test_type"."id") LIMIT 1
Limit  (cost=0.49..0.78 rows=1 width=1376) (actual rows=1.00 loops=1)
  Buffers: shared hit=4
  ->  Unique  (cost=0.49..28.04 rows=96 width=1376) (actual rows=1.00 loops=1)
        Buffers: shared hit=4
        ->  Incremental Sort  (cost=0.49..22.04 rows=96 width=1376) (actual rows=1.00 loops=1)
              Sort Key: dojo_test.id, dojo_test.engagement_id, dojo_test.lead_id, dojo_test.test_type_id, dojo_test.scan_type, dojo_test.title, dojo_test.description, dojo_test.target_start, dojo_test.target_end, dojo_test.percent_complete, dojo_test.environment_id, dojo_test.updated, dojo_test.created, dojo_test.version, dojo_test.build_id, dojo_test.commit_hash, dojo_test.branch_tag, dojo_test.api_scan_configuration_id, dojo_test.archived_at, dojo_test.archive_batch, dojo_test_type.name, dojo_test_type.static_tool, dojo_test_type.dynamic_tool, dojo_test_type.active, dojo_test_type.dynamically_generated
              Presorted Key: dojo_test.id
              Full-sort Groups: 1  Sort Method: quicksort  Average Memory: 29kB  Peak Memory: 29kB
              Buffers: shared hit=4
              ->  Nested Loop  (cost=0.30..17.72 rows=96 width=1376) (actual rows=33.00 loops=1)
                    Buffers: shared hit=4
                    ->  Index Scan using dojo_test_pkey on dojo_test  (cost=0.14..14.58 rows=96 width=1350) (actual rows=33.00 loops=1)
                          Index Searches: 1
                          Buffers: shared hit=2
                    ->  Memoize  (cost=0.16..0.38 rows=1 width=26) (actual rows=1.00 loops=33)
                          Cache Key: dojo_test.test_type_id
                          Cache Mode: logical
                          Hits: 32  Misses: 1  Evictions: 0  Overflows: 0  Memory Usage: 1kB
                          Buffers: shared hit=2
                          ->  Index Scan using dojo_test_type_pkey on dojo_test_type  (cost=0.15..0.37 rows=1 width=26) (actual rows=1.00 loops=1)
                                Index Cond: (id = dojo_test.test_type_id)
                                Index Searches: 1
                                Buffers: shared hit=2
Planning:
  Buffers: shared hit=5
Planning Time: 0.178 ms
Execution Time: 0.071 ms
### tests_1: dojo_finding_group / 370c05b6, observed 0.12 ms
SELECT <projection> FROM "dojo_finding_group" WHERE "dojo_finding_group"."test_id" IN (%s) ORDER BY "dojo_finding_group"."id" ASC
Sort  (cost=8.17..8.18 rows=1 width=568) (actual rows=0.00 loops=1)
  Sort Key: id
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=2
  ->  Index Scan using dojo_finding_group_test_id_841ea653 on dojo_finding_group  (cost=0.14..8.16 rows=1 width=568) (actual rows=0.00 loops=1)
        Index Cond: (test_id = 1)
        Index Searches: 1
        Buffers: shared hit=2
Planning:
  Buffers: shared hit=3
Planning Time: 0.022 ms
Execution Time: 0.016 ms
{"case": "tests_20", "url": "/api/v2/tests/?limit=20", "status": 200, "sql_count": 9, "sql_ms": 2.509, "fetch_ms": 0, "django_ms": 19.065, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_test / 34915665": 1, "dojo_test / 3547950c": 1, "dojo_notes / a311c4d9": 1, "dojo_fileupload / 3b175fe8": 1, "dojo_tagulous_test_tags / 7f6d0726": 1, "dojo_finding_group / c553c0cc": 1}, "bytes": 12884, "rows": 20}
### tests_20: dojo_notes / a311c4d9, observed 0.59 ms
SELECT <projection> FROM "dojo_notes" INNER JOIN "dojo_test_notes" ON ("dojo_notes"."id" = "dojo_test_notes"."notes_id") LEFT OUTER JOIN "dojo_note_type" ON ("dojo_notes"."note_type_id" = "dojo_note_type"."id") INNER JOIN "auth_user" ON ("dojo_notes"."author_id" = "auth_user"."id") LEFT OUTER JOIN "auth_user" T6 ON ("dojo_notes"."editor_id" = T6."id") WHERE "dojo_test_notes"."test_id" IN (<parameters>) ORDER BY "dojo_notes"."date" DESC
Sort  (cost=92.69..93.20 rows=204 width=4247) (actual rows=0.00 loops=1)
  Sort Key: dojo_notes.date DESC
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=3
  ->  Hash Left Join  (cost=69.63..84.87 rows=204 width=4247) (actual rows=0.00 loops=1)
        Hash Cond: (dojo_notes.editor_id = t6.id)
        Buffers: shared hit=3
        ->  Hash Join  (cost=58.73..73.42 rows=204 width=2480) (actual rows=0.00 loops=1)
              Hash Cond: (dojo_notes.author_id = auth_user.id)
              Buffers: shared hit=3
              ->  Hash Left Join  (cost=47.83..61.98 rows=204 width=713) (actual rows=0.00 loops=1)
                    Hash Cond: (dojo_notes.note_type_id = dojo_note_type.id)
                    Buffers: shared hit=2
                    ->  Hash Join  (cost=35.13..48.73 rows=204 width=70) (actual rows=0.00 loops=1)
                          Hash Cond: (dojo_test_notes.notes_id = dojo_notes.id)
                          Buffers: shared hit=2
                          ->  Bitmap Heap Scan on dojo_test_notes  (cost=5.78..18.84 rows=204 width=8) (actual rows=0.00 loops=1)
                                Recheck Cond: (test_id = ANY ('?'::integer[]))
                                Buffers: shared hit=2
                                ->  Bitmap Index Scan on dojo_test_notes_test_id_16d6acce  (cost=0.00..5.68 rows=204 width=0) (actual rows=0.00 loops=1)
                                      Index Cond: (test_id = ANY ('?'::integer[]))
                                      Index Searches: 1
                                      Buffers: shared hit=2
                          ->  Hash  (cost=18.60..18.60 rows=860 width=66) (never executed)
                                ->  Seq Scan on dojo_notes  (cost=0.00..18.60 rows=860 width=66) (never executed)
                    ->  Hash  (cost=11.20..11.20 rows=120 width=643) (never executed)
                          ->  Seq Scan on dojo_note_type  (cost=0.00..11.20 rows=120 width=643) (never executed)
              ->  Hash  (cost=10.40..10.40 rows=40 width=1767) (actual rows=1.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 9kB
                    Buffers: shared hit=1
                    ->  Seq Scan on auth_user  (cost=0.00..10.40 rows=40 width=1767) (actual rows=1.00 loops=1)
                          Buffers: shared hit=1
        ->  Hash  (cost=10.40..10.40 rows=40 width=1767) (never executed)
              ->  Seq Scan on auth_user t6  (cost=0.00..10.40 rows=40 width=1767) (never executed)
Planning:
  Buffers: shared hit=11
Planning Time: 0.248 ms
Execution Time: 0.071 ms
### tests_20: dojo_test / 3547950c, observed 0.43 ms
SELECT <projection> FROM "dojo_test" INNER JOIN "dojo_test_type" ON ("dojo_test"."test_type_id" = "dojo_test_type"."id") LIMIT 20
Limit  (cost=0.49..6.23 rows=20 width=1376) (actual rows=20.00 loops=1)
  Buffers: shared hit=4
  ->  Unique  (cost=0.49..28.04 rows=96 width=1376) (actual rows=20.00 loops=1)
        Buffers: shared hit=4
        ->  Incremental Sort  (cost=0.49..22.04 rows=96 width=1376) (actual rows=20.00 loops=1)
              Sort Key: dojo_test.id, dojo_test.engagement_id, dojo_test.lead_id, dojo_test.test_type_id, dojo_test.scan_type, dojo_test.title, dojo_test.description, dojo_test.target_start, dojo_test.target_end, dojo_test.percent_complete, dojo_test.environment_id, dojo_test.updated, dojo_test.created, dojo_test.version, dojo_test.build_id, dojo_test.commit_hash, dojo_test.branch_tag, dojo_test.api_scan_configuration_id, dojo_test.archived_at, dojo_test.archive_batch, dojo_test_type.name, dojo_test_type.static_tool, dojo_test_type.dynamic_tool, dojo_test_type.active, dojo_test_type.dynamically_generated
              Presorted Key: dojo_test.id
              Full-sort Groups: 1  Sort Method: quicksort  Average Memory: 29kB  Peak Memory: 29kB
              Buffers: shared hit=4
              ->  Nested Loop  (cost=0.30..17.72 rows=96 width=1376) (actual rows=33.00 loops=1)
                    Buffers: shared hit=4
                    ->  Index Scan using dojo_test_pkey on dojo_test  (cost=0.14..14.58 rows=96 width=1350) (actual rows=33.00 loops=1)
                          Index Searches: 1
                          Buffers: shared hit=2
                    ->  Memoize  (cost=0.16..0.38 rows=1 width=26) (actual rows=1.00 loops=33)
                          Cache Key: dojo_test.test_type_id
                          Cache Mode: logical
                          Hits: 32  Misses: 1  Evictions: 0  Overflows: 0  Memory Usage: 1kB
                          Buffers: shared hit=2
                          ->  Index Scan using dojo_test_type_pkey on dojo_test_type  (cost=0.15..0.37 rows=1 width=26) (actual rows=1.00 loops=1)
                                Index Cond: (id = dojo_test.test_type_id)
                                Index Searches: 1
                                Buffers: shared hit=2
Planning:
  Buffers: shared hit=5
Planning Time: 0.171 ms
Execution Time: 0.091 ms
### tests_20: dojo_finding_group / c553c0cc, observed 0.14 ms
SELECT <projection> FROM "dojo_finding_group" WHERE "dojo_finding_group"."test_id" IN (<parameters>) ORDER BY "dojo_finding_group"."id" ASC
Sort  (cost=12.43..12.48 rows=20 width=568) (actual rows=0.00 loops=1)
  Sort Key: id
  Sort Method: quicksort  Memory: 25kB
  ->  Seq Scan on dojo_finding_group  (cost=0.05..12.00 rows=20 width=568) (actual rows=0.00 loops=1)
        Filter: (test_id = ANY ('?'::integer[]))
Planning:
  Buffers: shared hit=3
Planning Time: 0.028 ms
Execution Time: 0.010 ms
{"case": "tests_100", "url": "/api/v2/tests/?limit=100", "status": 200, "sql_count": 9, "sql_ms": 4.42, "fetch_ms": 0, "django_ms": 43.189, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_test / 34915665": 1, "dojo_test / f651efd0": 1, "dojo_notes / c213cdc1": 1, "dojo_fileupload / 53abe2b5": 1, "dojo_tagulous_test_tags / 07086dd3": 1, "dojo_finding_group / 56062b6e": 1}, "bytes": 61461, "rows": 96}
### tests_100: dojo_notes / c213cdc1, observed 0.84 ms
SELECT <projection> FROM "dojo_notes" INNER JOIN "dojo_test_notes" ON ("dojo_notes"."id" = "dojo_test_notes"."notes_id") LEFT OUTER JOIN "dojo_note_type" ON ("dojo_notes"."note_type_id" = "dojo_note_type"."id") INNER JOIN "auth_user" ON ("dojo_notes"."author_id" = "auth_user"."id") LEFT OUTER JOIN "auth_user" T6 ON ("dojo_notes"."editor_id" = T6."id") WHERE "dojo_test_notes"."test_id" IN (<parameters>) ORDER BY "dojo_notes"."date" DESC
Sort  (cost=159.60..162.05 rows=979 width=4247) (actual rows=0.00 loops=1)
  Sort Key: dojo_notes.date DESC
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=3
  ->  Hash Left Join  (cost=75.83..110.97 rows=979 width=4247) (actual rows=0.00 loops=1)
        Hash Cond: (dojo_notes.editor_id = t6.id)
        Buffers: shared hit=3
        ->  Hash Join  (cost=64.93..97.45 rows=979 width=2480) (actual rows=0.00 loops=1)
              Hash Cond: (dojo_notes.author_id = auth_user.id)
              Buffers: shared hit=3
              ->  Hash Left Join  (cost=54.03..83.92 rows=979 width=713) (actual rows=0.00 loops=1)
                    Hash Cond: (dojo_notes.note_type_id = dojo_note_type.id)
                    Buffers: shared hit=2
                    ->  Hash Join  (cost=41.33..68.60 rows=979 width=70) (actual rows=0.00 loops=1)
                          Hash Cond: (dojo_test_notes.notes_id = dojo_notes.id)
                          Buffers: shared hit=2
                          ->  Bitmap Heap Scan on dojo_test_notes  (cost=11.98..36.66 rows=979 width=8) (actual rows=0.00 loops=1)
                                Recheck Cond: (test_id = ANY ('?'::integer[]))
                                Buffers: shared hit=2
                                ->  Bitmap Index Scan on dojo_test_notes_test_id_16d6acce  (cost=0.00..11.49 rows=979 width=0) (actual rows=0.00 loops=1)
                                      Index Cond: (test_id = ANY ('?'::integer[]))
                                      Index Searches: 1
                                      Buffers: shared hit=2
                          ->  Hash  (cost=18.60..18.60 rows=860 width=66) (never executed)
                                ->  Seq Scan on dojo_notes  (cost=0.00..18.60 rows=860 width=66) (never executed)
                    ->  Hash  (cost=11.20..11.20 rows=120 width=643) (never executed)
                          ->  Seq Scan on dojo_note_type  (cost=0.00..11.20 rows=120 width=643) (never executed)
              ->  Hash  (cost=10.40..10.40 rows=40 width=1767) (actual rows=1.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 9kB
                    Buffers: shared hit=1
                    ->  Seq Scan on auth_user  (cost=0.00..10.40 rows=40 width=1767) (actual rows=1.00 loops=1)
                          Buffers: shared hit=1
        ->  Hash  (cost=10.40..10.40 rows=40 width=1767) (never executed)
              ->  Seq Scan on auth_user t6  (cost=0.00..10.40 rows=40 width=1767) (never executed)
Planning:
  Buffers: shared hit=11
Planning Time: 0.319 ms
Execution Time: 0.098 ms
### tests_100: dojo_test / f651efd0, observed 0.64 ms
SELECT <projection> FROM "dojo_test" INNER JOIN "dojo_test_type" ON ("dojo_test"."test_type_id" = "dojo_test_type"."id") LIMIT 100
Limit  (cost=12.10..13.06 rows=96 width=1376) (actual rows=96.00 loops=1)
  Buffers: shared hit=4
  ->  HashAggregate  (cost=12.10..13.06 rows=96 width=1376) (actual rows=96.00 loops=1)
        Group Key: dojo_test.id, dojo_test.engagement_id, dojo_test.lead_id, dojo_test.test_type_id, dojo_test.scan_type, dojo_test.title, dojo_test.description, dojo_test.target_start, dojo_test.target_end, dojo_test.percent_complete, dojo_test.environment_id, dojo_test.updated, dojo_test.created, dojo_test.version, dojo_test.build_id, dojo_test.commit_hash, dojo_test.branch_tag, dojo_test.api_scan_configuration_id, dojo_test.archived_at, dojo_test.archive_batch, dojo_test_type.name, dojo_test_type.static_tool, dojo_test_type.dynamic_tool, dojo_test_type.active, dojo_test_type.dynamically_generated
        Batches: 1  Memory Usage: 96kB
        Buffers: shared hit=4
        ->  Nested Loop  (cost=0.16..6.10 rows=96 width=1376) (actual rows=96.00 loops=1)
              Buffers: shared hit=4
              ->  Seq Scan on dojo_test  (cost=0.00..2.96 rows=96 width=1350) (actual rows=96.00 loops=1)
                    Buffers: shared hit=2
              ->  Memoize  (cost=0.16..0.38 rows=1 width=26) (actual rows=1.00 loops=96)
                    Cache Key: dojo_test.test_type_id
                    Cache Mode: logical
                    Hits: 95  Misses: 1  Evictions: 0  Overflows: 0  Memory Usage: 1kB
                    Buffers: shared hit=2
                    ->  Index Scan using dojo_test_type_pkey on dojo_test_type  (cost=0.15..0.37 rows=1 width=26) (actual rows=1.00 loops=1)
                          Index Cond: (id = dojo_test.test_type_id)
                          Index Searches: 1
                          Buffers: shared hit=2
Planning:
  Buffers: shared hit=5
Planning Time: 0.190 ms
Execution Time: 0.161 ms
### tests_100: dojo_tagulous_test_tags / 07086dd3, observed 0.55 ms
SELECT <projection> FROM "dojo_tagulous_test_tags" INNER JOIN "dojo_test_tags" ON ("dojo_tagulous_test_tags"."id" = "dojo_test_tags"."tagulous_test_tags_id") WHERE "dojo_test_tags"."test_id" IN (<parameters>) ORDER BY "dojo_tagulous_test_tags"."name" ASC
Sort  (cost=100.62..103.07 rows=979 width=647) (actual rows=0.00 loops=1)
  Sort Key: dojo_tagulous_test_tags.name
  Sort Method: quicksort  Memory: 25kB
  ->  Hash Join  (cost=24.68..51.99 rows=979 width=647) (actual rows=0.00 loops=1)
        Hash Cond: (dojo_test_tags.tagulous_test_tags_id = dojo_tagulous_test_tags.id)
        ->  Bitmap Heap Scan on dojo_test_tags  (cost=11.98..36.66 rows=979 width=8) (never executed)
              Recheck Cond: (test_id = ANY ('?'::integer[]))
              ->  Bitmap Index Scan on dojo_test_tags_test_id_84333c06  (cost=0.00..11.49 rows=979 width=0) (never executed)
                    Index Cond: (test_id = ANY ('?'::integer[]))
                    Index Searches: 0
        ->  Hash  (cost=11.20..11.20 rows=120 width=643) (actual rows=0.00 loops=1)
              Buckets: 1024  Batches: 1  Memory Usage: 8kB
              ->  Seq Scan on dojo_tagulous_test_tags  (cost=0.00..11.20 rows=120 width=643) (actual rows=0.00 loops=1)
Planning:
  Buffers: shared hit=10
Planning Time: 0.100 ms
Execution Time: 0.021 ms
{"case": "test_detail_large", "url": "/api/v2/tests/1/", "status": 200, "sql_count": 8, "sql_ms": 2.215, "fetch_ms": 0, "django_ms": 13.332, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_test / 158c5a93": 1, "dojo_notes / 62704bb0": 1, "dojo_fileupload / 64b43434": 1, "dojo_tagulous_test_tags / 87c84f78": 1, "dojo_finding_group / 370c05b6": 1}, "bytes": 651, "rows": 1}
### test_detail_large: dojo_test / 158c5a93, observed 0.53 ms
SELECT <projection> FROM "dojo_test" INNER JOIN "dojo_test_type" ON ("dojo_test"."test_type_id" = "dojo_test_type"."id") WHERE "dojo_test"."id" = %s LIMIT 21
Limit  (cost=11.20..11.26 rows=1 width=1376) (actual rows=1.00 loops=1)
  Buffers: shared hit=5
  ->  Unique  (cost=11.20..11.26 rows=1 width=1376) (actual rows=1.00 loops=1)
        Buffers: shared hit=5
        ->  Sort  (cost=11.20..11.20 rows=1 width=1376) (actual rows=1.00 loops=1)
              Sort Key: dojo_test.engagement_id, dojo_test.lead_id, dojo_test.test_type_id, dojo_test.scan_type, dojo_test.title, dojo_test.description, dojo_test.target_start, dojo_test.target_end, dojo_test.percent_complete, dojo_test.environment_id, dojo_test.updated, dojo_test.created, dojo_test.version, dojo_test.build_id, dojo_test.commit_hash, dojo_test.branch_tag, dojo_test.api_scan_configuration_id, dojo_test.archived_at, dojo_test.archive_batch, dojo_test_type.name, dojo_test_type.static_tool, dojo_test_type.dynamic_tool, dojo_test_type.active, dojo_test_type.dynamically_generated
              Sort Method: quicksort  Memory: 25kB
              Buffers: shared hit=5
              ->  Hash Join  (cost=3.21..11.19 rows=1 width=1376) (actual rows=1.00 loops=1)
                    Hash Cond: (dojo_test_type.id = dojo_test.test_type_id)
                    Buffers: shared hit=5
                    ->  Seq Scan on dojo_test_type  (cost=0.00..6.93 rows=393 width=26) (actual rows=394.00 loops=1)
                          Buffers: shared hit=3
                    ->  Hash  (cost=3.20..3.20 rows=1 width=1350) (actual rows=1.00 loops=1)
                          Buckets: 1024  Batches: 1  Memory Usage: 9kB
                          Buffers: shared hit=2
                          ->  Seq Scan on dojo_test  (cost=0.00..3.20 rows=1 width=1350) (actual rows=1.00 loops=1)
                                Filter: (id = 1)
                                Rows Removed by Filter: 95
                                Buffers: shared hit=2
Planning:
  Buffers: shared hit=5
Planning Time: 0.202 ms
Execution Time: 0.094 ms
### test_detail_large: dojo_notes / 62704bb0, observed 0.52 ms
SELECT <projection> FROM "dojo_notes" INNER JOIN "dojo_test_notes" ON ("dojo_notes"."id" = "dojo_test_notes"."notes_id") LEFT OUTER JOIN "dojo_note_type" ON ("dojo_notes"."note_type_id" = "dojo_note_type"."id") INNER JOIN "auth_user" ON ("dojo_notes"."author_id" = "auth_user"."id") LEFT OUTER JOIN "auth_user" T6 ON ("dojo_notes"."editor_id" = T6."id") WHERE "dojo_test_notes"."test_id" IN (%s) ORDER BY "dojo_notes"."date" DESC
Sort  (cost=42.33..42.36 rows=10 width=4247) (actual rows=0.00 loops=1)
  Sort Key: dojo_notes.date DESC
  Sort Method: quicksort  Memory: 25kB
  ->  Nested Loop Left Join  (cost=15.33..42.16 rows=10 width=4247) (actual rows=0.00 loops=1)
        ->  Nested Loop  (cost=15.19..40.03 rows=10 width=2480) (actual rows=0.00 loops=1)
              ->  Nested Loop Left Join  (cost=15.05..37.89 rows=10 width=713) (actual rows=0.00 loops=1)
                    ->  Hash Join  (cost=14.91..35.78 rows=10 width=70) (actual rows=0.00 loops=1)
                          Hash Cond: (dojo_notes.id = dojo_test_notes.notes_id)
                          ->  Seq Scan on dojo_notes  (cost=0.00..18.60 rows=860 width=66) (actual rows=0.00 loops=1)
                          ->  Hash  (cost=14.79..14.79 rows=10 width=8) (never executed)
                                ->  Bitmap Heap Scan on dojo_test_notes  (cost=4.23..14.79 rows=10 width=8) (never executed)
                                      Recheck Cond: (test_id = 1)
                                      ->  Bitmap Index Scan on dojo_test_notes_test_id_16d6acce  (cost=0.00..4.23 rows=10 width=0) (never executed)
                                            Index Cond: (test_id = 1)
                                            Index Searches: 0
                    ->  Index Scan using dojo_note_type_pkey on dojo_note_type  (cost=0.14..0.21 rows=1 width=643) (never executed)
                          Index Cond: (id = dojo_notes.note_type_id)
                          Index Searches: 0
              ->  Index Scan using auth_user_pkey on auth_user  (cost=0.14..0.21 rows=1 width=1767) (never executed)
                    Index Cond: (id = dojo_notes.author_id)
                    Index Searches: 0
        ->  Index Scan using auth_user_pkey on auth_user t6  (cost=0.14..0.21 rows=1 width=1767) (never executed)
              Index Cond: (id = dojo_notes.editor_id)
              Index Searches: 0
Planning:
  Buffers: shared hit=11
Planning Time: 0.257 ms
Execution Time: 0.051 ms
### test_detail_large: dojo_finding_group / 370c05b6, observed 0.13 ms
SELECT <projection> FROM "dojo_finding_group" WHERE "dojo_finding_group"."test_id" IN (%s) ORDER BY "dojo_finding_group"."id" ASC
Sort  (cost=8.17..8.18 rows=1 width=568) (actual rows=0.00 loops=1)
  Sort Key: id
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=2
  ->  Index Scan using dojo_finding_group_test_id_841ea653 on dojo_finding_group  (cost=0.14..8.16 rows=1 width=568) (actual rows=0.00 loops=1)
        Index Cond: (test_id = 1)
        Index Searches: 1
        Buffers: shared hit=2
Planning:
  Buffers: shared hit=3
Planning Time: 0.021 ms
Execution Time: 0.026 ms
{"case": "findings_product", "url": "/api/v2/findings/?product=2&limit=100", "status": 200, "sql_count": 24, "sql_ms": 54.586, "fetch_ms": 0, "django_ms": 272.501, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_finding / b029f9bf": 1, "dojo_finding / 7d4d8a5d": 1, "dojo_locationfindingreference / 7232ecb7": 1, "auth_user / c717d892": 1, "dojo_test_type / 9210c588": 1, "dojo_notes / 24579f35": 1, "dojo_risk_acceptance / 40c15205": 1, "dojo_test / 09f5be84": 1, "dojo_tagulous_finding_tags / 6e492e55": 1, "dojo_jira_issue / b01edc2a": 1, "dojo_finding_group / baac0f4d": 1, "dojo_fileupload / dc5354fd": 1, "dojo_burprawrequestresponse / 4c41c852": 1, "dojo_endpoint_status / bd0088ca": 1, "dojo_dojometa / 0ad748ba": 1, "dojo_test_type / 7a604a36": 1, "dojo_engagement / 2e5e5cc1": 1, "dojo_product / b10d7cde": 1, "dojo_product_type / d8070c78": 1, "dojo_finding_cwe / 8168aedd": 1, "dojo_findingvulnerabilityreference / 787dc19d": 1}, "bytes": 289452, "rows": 100}
### findings_product: dojo_finding / b029f9bf, observed 44.09 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE "dojo_engagement"."product_id" IN (%s)
Aggregate  (cost=4736.87..4736.88 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=13175
  ->  Nested Loop  (cost=0.70..4487.01 rows=99944 width=0) (actual rows=633794.00 loops=1)
        Buffers: shared hit=13175
        ->  Nested Loop  (cost=0.28..24.18 rows=10 width=4) (actual rows=8.00 loops=1)
              Join Filter: (dojo_engagement.id = dojo_test.engagement_id)
              Rows Removed by Join Filter: 180
              Buffers: shared hit=5
              ->  Index Scan using dojo_test_pkey on dojo_test  (cost=0.14..14.58 rows=96 width=8) (actual rows=96.00 loops=1)
                    Index Searches: 1
                    Buffers: shared hit=3
              ->  Materialize  (cost=0.14..8.16 rows=1 width=4) (actual rows=1.96 loops=96)
                    Storage: Memory  Maximum Storage: 17kB
                    Buffers: shared hit=2
                    ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                          Index Cond: (product_id = 2)
                          Index Searches: 1
                          Buffers: shared hit=2
        ->  Index Only Scan using dojo_finding_test_id_ef8ec5fc on dojo_finding  (cost=0.42..342.17 rows=10411 width=4) (actual rows=79224.25 loops=8)
              Index Cond: (test_id = dojo_test.id)
              Heap Fetches: 16538
              Index Searches: 8
              Buffers: shared hit=13170
Planning:
  Buffers: shared hit=8
Planning Time: 0.377 ms
Execution Time: 68.392 ms
### findings_product: dojo_finding / 7d4d8a5d, observed 1.67 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE "dojo_engagement"."product_id" IN (%s) ORDER BY "dojo_finding"."id" ASC LIMIT 100
Limit  (cost=0.71..191.84 rows=100 width=5463) (actual rows=100.00 loops=1)
  Buffers: shared hit=126
  ->  Nested Loop  (cost=0.71..191016.72 rows=99944 width=5463) (actual rows=100.00 loops=1)
        Join Filter: (dojo_engagement.id = dojo_test.engagement_id)
        Rows Removed by Join Filter: 156
        Buffers: shared hit=126
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
        ->  Materialize  (cost=0.14..8.16 rows=1 width=4) (actual rows=1.70 loops=151)
              Storage: Memory  Maximum Storage: 17kB
              Buffers: shared hit=2
              ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                    Index Cond: (product_id = 2)
                    Index Searches: 1
                    Buffers: shared hit=2
Planning:
  Buffers: shared hit=8
Planning Time: 0.518 ms
Execution Time: 0.273 ms
### findings_product: dojo_findingvulnerabilityreference / 787dc19d, observed 0.86 ms
SELECT <projection> FROM "dojo_findingvulnerabilityreference" INNER JOIN "dojo_vulnerability" ON ("dojo_findingvulnerabilityreference"."vulnerability_id" = "dojo_vulnerability"."id") WHERE "dojo_findingvulnerabilityreference"."finding_id" IN (<parameters>) ORDER BY "dojo_findingvulnerabilityreference"."order" ASC
Sort  (cost=73.81..75.19 rows=550 width=190) (actual rows=0.00 loops=1)
  Sort Key: dojo_findingvulnerabilityreference."order"
  Sort Method: quicksort  Memory: 25kB
  ->  Hash Join  (cost=20.82..48.78 rows=550 width=190) (actual rows=0.00 loops=1)
        Hash Cond: (dojo_findingvulnerabilityreference.vulnerability_id = dojo_vulnerability.id)
        ->  Seq Scan on dojo_findingvulnerabilityreference  (cost=0.25..26.75 rows=550 width=46) (actual rows=0.00 loops=1)
              Filter: (finding_id = ANY ('?'::integer[]))
        ->  Hash  (cost=14.70..14.70 rows=470 width=144) (never executed)
              ->  Seq Scan on dojo_vulnerability  (cost=0.00..14.70 rows=470 width=144) (never executed)
Planning:
  Buffers: shared hit=15
Planning Time: 0.141 ms
Execution Time: 0.036 ms
{"case": "findings_product_active", "url": "/api/v2/findings/?product=2&active=true&limit=100", "status": 200, "sql_count": 24, "sql_ms": 48.397, "fetch_ms": 0, "django_ms": 148.119, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_finding / d3aa94a6": 1, "dojo_finding / 822fae3c": 1, "dojo_locationfindingreference / 7232ecb7": 1, "auth_user / c717d892": 1, "dojo_test_type / 9210c588": 1, "dojo_notes / 24579f35": 1, "dojo_risk_acceptance / 40c15205": 1, "dojo_test / 09f5be84": 1, "dojo_tagulous_finding_tags / 6e492e55": 1, "dojo_jira_issue / b01edc2a": 1, "dojo_finding_group / baac0f4d": 1, "dojo_fileupload / dc5354fd": 1, "dojo_burprawrequestresponse / 4c41c852": 1, "dojo_endpoint_status / bd0088ca": 1, "dojo_dojometa / 0ad748ba": 1, "dojo_test_type / 7a604a36": 1, "dojo_engagement / 2e5e5cc1": 1, "dojo_product / b10d7cde": 1, "dojo_product_type / d8070c78": 1, "dojo_finding_cwe / 8168aedd": 1, "dojo_findingvulnerabilityreference / 787dc19d": 1}, "bytes": 290572, "rows": 100}
### findings_product_active: dojo_finding / d3aa94a6, observed 34.37 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_finding"."active" AND "dojo_engagement"."product_id" IN (%s))
Aggregate  (cost=4460.10..4460.11 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=12926
  ->  Nested Loop  (cost=0.70..4250.77 rows=83730 width=0) (actual rows=532569.00 loops=1)
        Buffers: shared hit=12926
        ->  Nested Loop  (cost=0.28..24.18 rows=10 width=4) (actual rows=8.00 loops=1)
              Join Filter: (dojo_engagement.id = dojo_test.engagement_id)
              Rows Removed by Join Filter: 180
              Buffers: shared hit=5
              ->  Index Scan using dojo_test_pkey on dojo_test  (cost=0.14..14.58 rows=96 width=8) (actual rows=96.00 loops=1)
                    Index Searches: 1
                    Buffers: shared hit=3
              ->  Materialize  (cost=0.14..8.16 rows=1 width=4) (actual rows=1.96 loops=96)
                    Storage: Memory  Maximum Storage: 17kB
                    Buffers: shared hit=2
                    ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
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
Planning Time: 0.336 ms
Execution Time: 47.373 ms
### findings_product_active: dojo_burprawrequestresponse / 4c41c852, observed 3.26 ms
SELECT <projection> FROM "dojo_burprawrequestresponse" WHERE "dojo_burprawrequestresponse"."finding_id" IN (<parameters>)
Seq Scan on dojo_burprawrequestresponse  (cost=0.25..22.40 rows=405 width=72) (actual rows=0.00 loops=1)
  Filter: (finding_id = ANY ('?'::integer[]))
Planning:
  Buffers: shared hit=2
Planning Time: 0.049 ms
Execution Time: 0.006 ms
### findings_product_active: dojo_finding / 822fae3c, observed 1.57 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_finding"."active" AND "dojo_engagement"."product_id" IN (%s)) ORDER BY "dojo_finding"."id" ASC LIMIT 100
Limit  (cost=0.71..221.13 rows=100 width=5463) (actual rows=100.00 loops=1)
  Buffers: shared hit=128
  ->  Nested Loop  (cost=0.71..184555.85 rows=83730 width=5463) (actual rows=100.00 loops=1)
        Join Filter: (dojo_engagement.id = dojo_test.engagement_id)
        Rows Removed by Join Filter: 153
        Buffers: shared hit=128
        ->  Nested Loop  (cost=0.58..171988.27 rows=837295 width=5467) (actual rows=149.00 loops=1)
              Buffers: shared hit=126
              ->  Index Scan using dojo_finding_pkey on dojo_finding  (cost=0.42..151168.53 rows=837295 width=5463) (actual rows=149.00 loops=1)
                    Filter: active
                    Rows Removed by Filter: 24
                    Index Searches: 1
                    Buffers: shared hit=30
              ->  Memoize  (cost=0.15..0.17 rows=1 width=8) (actual rows=1.00 loops=149)
                    Cache Key: dojo_finding.test_id
                    Cache Mode: logical
                    Hits: 101  Misses: 48  Evictions: 0  Overflows: 0  Memory Usage: 6kB
                    Buffers: shared hit=96
                    ->  Index Scan using dojo_test_pkey on dojo_test  (cost=0.14..0.16 rows=1 width=8) (actual rows=1.00 loops=48)
                          Index Cond: (id = dojo_finding.test_id)
                          Index Searches: 48
                          Buffers: shared hit=96
        ->  Materialize  (cost=0.14..8.16 rows=1 width=4) (actual rows=1.70 loops=149)
              Storage: Memory  Maximum Storage: 17kB
              Buffers: shared hit=2
              ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                    Index Cond: (product_id = 2)
                    Index Searches: 1
                    Buffers: shared hit=2
Planning:
  Buffers: shared hit=8
Planning Time: 0.376 ms
Execution Time: 0.236 ms
{"case": "findings_product_fast", "url": "/api/v2/findings/?product=2&active=true&limit=100&offset=500000&fast_offset=1", "status": 200, "sql_count": 25, "sql_ms": 944.334, "fetch_ms": 0, "django_ms": 1035.394, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_finding / d3aa94a6": 1, "dojo_finding / 33651ad9": 1, "dojo_finding / bbadeec9": 1, "dojo_locationfindingreference / 7232ecb7": 1, "auth_user / c717d892": 1, "dojo_test_type / 9210c588": 1, "dojo_notes / 24579f35": 1, "dojo_risk_acceptance / 40c15205": 1, "dojo_test / 09f5be84": 1, "dojo_tagulous_finding_tags / 6e492e55": 1, "dojo_jira_issue / b01edc2a": 1, "dojo_finding_group / baac0f4d": 1, "dojo_fileupload / dc5354fd": 1, "dojo_burprawrequestresponse / 4c41c852": 1, "dojo_endpoint_status / bd0088ca": 1, "dojo_dojometa / 0ad748ba": 1, "dojo_test_type / 7a604a36": 1, "dojo_engagement / 2e5e5cc1": 1, "dojo_product / b10d7cde": 1, "dojo_product_type / d8070c78": 1, "dojo_finding_cwe / 8168aedd": 1, "dojo_findingvulnerabilityreference / 787dc19d": 1}, "bytes": 294786, "rows": 100}
### findings_product_fast: dojo_finding / 33651ad9, observed 872.00 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_finding"."active" AND "dojo_engagement"."product_id" IN (%s)) ORDER BY "dojo_finding"."id" ASC LIMIT 100 OFFSET 500000
Limit  (cost=58380.73..58380.74 rows=1 width=4) (actual rows=100.00 loops=1)
  Buffers: shared hit=6 read=422806, temp read=775 written=787
  ->  Sort  (cost=58171.41..58380.73 rows=83730 width=4) (actual rows=500100.00 loops=1)
        Sort Key: dojo_finding.id
        Sort Method: external merge  Disk: 6272kB
        Buffers: shared hit=6 read=422806, temp read=775 written=787
        ->  Nested Loop  (cost=114.88..51325.03 rows=83730 width=4) (actual rows=532569.00 loops=1)
              Buffers: shared hit=6 read=422806
              ->  Nested Loop  (cost=0.14..12.31 rows=10 width=4) (actual rows=8.00 loops=1)
                    Join Filter: (dojo_engagement.id = dojo_test.engagement_id)
                    Rows Removed by Join Filter: 184
                    Buffers: shared hit=6
                    ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                          Index Cond: (product_id = 2)
                          Index Searches: 1
                          Buffers: shared hit=2
                    ->  Seq Scan on dojo_test  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=2)
                          Buffers: shared hit=4
              ->  Bitmap Heap Scan on dojo_finding  (cost=114.74..5044.05 rows=8722 width=8) (actual rows=66571.12 loops=8)
                    Recheck Cond: ((dojo_test.id = test_id) AND active)
                    Heap Blocks: exact=422365
                    Buffers: shared read=422806
                    ->  Bitmap Index Scan on dojo_findin_test_id_bfc47c_idx  (cost=0.00..112.56 rows=8722 width=0) (actual rows=66571.12 loops=8)
                          Index Cond: ((test_id = dojo_test.id) AND (active = true))
                          Index Searches: 8
                          Buffers: shared read=441
Planning:
  Buffers: shared hit=8
Planning Time: 0.401 ms
Execution Time: 886.001 ms
### findings_product_fast: dojo_finding / d3aa94a6, observed 50.17 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_finding"."active" AND "dojo_engagement"."product_id" IN (%s))
Aggregate  (cost=4460.10..4460.11 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=10632 read=2294
  ->  Nested Loop  (cost=0.70..4250.77 rows=83730 width=0) (actual rows=532569.00 loops=1)
        Buffers: shared hit=10632 read=2294
        ->  Nested Loop  (cost=0.28..24.18 rows=10 width=4) (actual rows=8.00 loops=1)
              Join Filter: (dojo_engagement.id = dojo_test.engagement_id)
              Rows Removed by Join Filter: 180
              Buffers: shared hit=4 read=1
              ->  Index Scan using dojo_test_pkey on dojo_test  (cost=0.14..14.58 rows=96 width=8) (actual rows=96.00 loops=1)
                    Index Searches: 1
                    Buffers: shared hit=3
              ->  Materialize  (cost=0.14..8.16 rows=1 width=4) (actual rows=1.96 loops=96)
                    Storage: Memory  Maximum Storage: 17kB
                    Buffers: shared hit=1 read=1
                    ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
                          Index Cond: (product_id = 2)
                          Index Searches: 1
                          Buffers: shared hit=1 read=1
        ->  Index Only Scan using dojo_findin_test_id_bfc47c_idx on dojo_finding  (cost=0.42..335.44 rows=8722 width=4) (actual rows=66571.12 loops=8)
              Index Cond: ((test_id = dojo_test.id) AND (active = true))
              Heap Fetches: 13900
              Index Searches: 8
              Buffers: shared hit=10628 read=2293
Planning:
  Buffers: shared hit=3 read=5
Planning Time: 0.382 ms
Execution Time: 51.737 ms
### findings_product_fast: dojo_finding / bbadeec9, observed 2.33 ms
SELECT <projection> FROM "dojo_finding" INNER JOIN "dojo_test" ON ("dojo_finding"."test_id" = "dojo_test"."id") INNER JOIN "dojo_engagement" ON ("dojo_test"."engagement_id" = "dojo_engagement"."id") WHERE ("dojo_finding"."active" AND "dojo_engagement"."product_id" IN (%s) AND "dojo_finding"."id" IN (<parameters>)) ORDER BY "dojo_finding"."id" ASC
Sort  (cost=469.97..469.99 rows=8 width=5463) (actual rows=100.00 loops=1)
  Sort Key: dojo_finding.id
  Sort Method: quicksort  Memory: 119kB
  Buffers: shared hit=44 read=16
  ->  Nested Loop  (cost=4.72..469.85 rows=8 width=5463) (actual rows=100.00 loops=1)
        Join Filter: (dojo_engagement.id = dojo_test.engagement_id)
        Rows Removed by Join Filter: 100
        Buffers: shared hit=44 read=16
        ->  Index Scan using dojo_engagement_product_id_c46b1b11 on dojo_engagement  (cost=0.14..8.15 rows=1 width=4) (actual rows=2.00 loops=1)
              Index Cond: (product_id = 2)
              Index Searches: 1
              Buffers: shared hit=2
        ->  Hash Join  (cost=4.58..460.64 rows=84 width=5467) (actual rows=100.00 loops=2)
              Hash Cond: (dojo_finding.test_id = dojo_test.id)
              Buffers: shared hit=42 read=16
              ->  Index Scan using dojo_finding_pkey on dojo_finding  (cost=0.42..456.25 rows=84 width=5463) (actual rows=100.00 loops=2)
                    Index Cond: (id = ANY ('?'::integer[]))
                    Filter: active
                    Index Searches: 2
                    Buffers: shared hit=40 read=16
              ->  Hash  (cost=2.96..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 12kB
                    Buffers: shared hit=2
                    ->  Seq Scan on dojo_test  (cost=0.00..2.96 rows=96 width=8) (actual rows=96.00 loops=1)
                          Buffers: shared hit=2
Planning:
  Buffers: shared hit=8
Planning Time: 0.417 ms
Execution Time: 0.390 ms
