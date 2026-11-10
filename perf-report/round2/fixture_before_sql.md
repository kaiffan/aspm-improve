141 objects imported automatically (use -v 2 for details).

{"case": "engagements_1", "url": "/api/v2/engagements/?product=9&limit=1", "status": 200, "sql_count": 10, "sql_ms": 2.747, "fetch_ms": 0, "django_ms": 11.729, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_product / 0f2bb9c2": 1, "dojo_engagement / 36b4f668": 1, "dojo_engagement / d9dfd3d3": 1, "dojo_notes / c8142c5a": 1, "dojo_risk_acceptance / eb993df3": 1, "dojo_fileupload / 396fcebb": 1, "dojo_tagulous_engagement_tags / 55e9f977": 1}, "bytes": 975, "rows": 1}
### engagements_1: dojo_engagement / 36b4f668, observed 0.58 ms
SELECT <projection> FROM (SELECT DISTINCT "dojo_engagement"."id" AS "col1", "dojo_engagement"."created" AS "col2", "dojo_engagement"."updated" AS "col3", "dojo_engagement"."name" AS "col4", "dojo_engagement"."description" AS "col5", "dojo_engagement"."version" AS "col6", "dojo_engagement"."first_contacted" AS "col7", "dojo_engagement"."target_start" AS "col8", "dojo_engagement"."target_end" AS "col9", "dojo_engagement"."lead_id" AS "col10", "dojo_engagement"."requester_id" AS "col11", "dojo_engagement"."preset_id" AS "col12", "dojo_engagement"."reason" AS "col13", "dojo_engagement"."report_type_id" AS "col14", "dojo_engagement"."product_id" AS "col15", "dojo_engagement"."active" AS "col16", "dojo_engagement"."tracker" AS "col17", "dojo_engagement"."test_strategy" AS "col18", "dojo_engagement"."threat_model" AS "col19", "dojo_engagement"."api_test" AS "col20", "dojo_engagement"."pen_test" AS "col21", "dojo_engagement"."check_list" AS "col22", "dojo_engagement"."status" AS "col23", "dojo_engagement"."progress" AS "col24", "dojo_engagement"."tmodel_path" AS "col25", "dojo_engagement"."done_testing" AS "col26", "dojo_engagement"."engagement_type" AS "col27", "dojo_engagement"."build_id" AS "col28", "dojo_engagement"."commit_hash" AS "col29", "dojo_engagement"."branch_tag" AS "col30", "dojo_engagement"."source_code_management_uri" AS "col31", "dojo_engagement"."cicd_scm_server_id" A
Aggregate  (cost=2.14..2.15 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=2
  ->  Unique  (cost=2.03..2.13 rows=1 width=5495) (actual rows=100.00 loops=1)
        Buffers: shared hit=2
        ->  Sort  (cost=2.03..2.04 rows=1 width=5495) (actual rows=100.00 loops=1)
              Sort Key: dojo_engagement.id, dojo_engagement.created, dojo_engagement.updated, dojo_engagement.name, dojo_engagement.description, dojo_engagement.version, dojo_engagement.first_contacted, dojo_engagement.target_start, dojo_engagement.target_end, dojo_engagement.lead_id, dojo_engagement.requester_id, dojo_engagement.preset_id, dojo_engagement.reason, dojo_engagement.report_type_id, dojo_engagement.active, dojo_engagement.tracker, dojo_engagement.test_strategy, dojo_engagement.threat_model, dojo_engagement.api_test, dojo_engagement.pen_test, dojo_engagement.check_list, dojo_engagement.status, dojo_engagement.progress, dojo_engagement.tmodel_path, dojo_engagement.done_testing, dojo_engagement.engagement_type, dojo_engagement.build_id, dojo_engagement.commit_hash, dojo_engagement.branch_tag, dojo_engagement.source_code_management_uri, dojo_engagement.cicd_scm_server_id, dojo_engagement.cicd_build_server_id, dojo_engagement.cicd_orchestration_engine_id, dojo_engagement.deduplication_on_engagement, dojo_engagement.archived_at, dojo_engagement.archive_batch
              Sort Method: quicksort  Memory: 38kB
              Buffers: shared hit=2
              ->  Seq Scan on dojo_engagement  (cost=0.00..2.02 rows=1 width=5495) (actual rows=100.00 loops=1)
                    Filter: (product_id = 9)
                    Buffers: shared hit=2
Planning:
  Buffers: shared hit=1
Planning Time: 0.187 ms
Execution Time: 0.140 ms
### engagements_1: dojo_notes / c8142c5a, observed 0.53 ms
SELECT <projection> FROM "dojo_notes" INNER JOIN "dojo_engagement_notes" ON ("dojo_notes"."id" = "dojo_engagement_notes"."notes_id") LEFT OUTER JOIN "dojo_note_type" ON ("dojo_notes"."note_type_id" = "dojo_note_type"."id") INNER JOIN "auth_user" ON ("dojo_notes"."author_id" = "auth_user"."id") LEFT OUTER JOIN "auth_user" T6 ON ("dojo_notes"."editor_id" = T6."id") WHERE "dojo_engagement_notes"."engagement_id" IN (%s) ORDER BY "dojo_notes"."date" DESC
Sort  (cost=40.34..40.36 rows=10 width=4247) (actual rows=0.00 loops=1)
  Sort Key: dojo_notes.date DESC
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=2
  ->  Hash Left Join  (cost=17.23..40.17 rows=10 width=4247) (actual rows=0.00 loops=1)
        Hash Cond: (dojo_notes.editor_id = t6.id)
        Buffers: shared hit=2
        ->  Hash Join  (cost=16.14..39.05 rows=10 width=2480) (actual rows=0.00 loops=1)
              Hash Cond: (dojo_notes.author_id = auth_user.id)
              Buffers: shared hit=2
              ->  Nested Loop Left Join  (cost=15.05..37.94 rows=10 width=713) (actual rows=0.00 loops=1)
                    Buffers: shared hit=1
                    ->  Hash Join  (cost=14.91..35.78 rows=10 width=70) (actual rows=0.00 loops=1)
                          Hash Cond: (dojo_notes.id = dojo_engagement_notes.notes_id)
                          Buffers: shared hit=1
                          ->  Seq Scan on dojo_notes  (cost=0.00..18.60 rows=860 width=66) (actual rows=0.00 loops=1)
                                Buffers: shared hit=1
                          ->  Hash  (cost=14.79..14.79 rows=10 width=8) (never executed)
                                ->  Bitmap Heap Scan on dojo_engagement_notes  (cost=4.23..14.79 rows=10 width=8) (never executed)
                                      Recheck Cond: (engagement_id = 13)
                                      ->  Bitmap Index Scan on dojo_engagement_notes_engagement_id_6d165427  (cost=0.00..4.23 rows=10 width=0) (never executed)
                                            Index Cond: (engagement_id = 13)
                                            Index Searches: 0
                    ->  Index Scan using dojo_note_type_pkey on dojo_note_type  (cost=0.14..0.22 rows=1 width=643) (never executed)
                          Index Cond: (id = dojo_notes.note_type_id)
                          Index Searches: 0
              ->  Hash  (cost=1.04..1.04 rows=4 width=1767) (actual rows=1.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 9kB
                    Buffers: shared hit=1
                    ->  Seq Scan on auth_user  (cost=0.00..1.04 rows=4 width=1767) (actual rows=1.00 loops=1)
                          Buffers: shared hit=1
        ->  Hash  (cost=1.04..1.04 rows=4 width=1767) (never executed)
              ->  Seq Scan on auth_user t6  (cost=0.00..1.04 rows=4 width=1767) (never executed)
Planning Time: 0.252 ms
Execution Time: 0.088 ms
{"case": "engagements_20", "url": "/api/v2/engagements/?product=9&limit=20", "status": 200, "sql_count": 10, "sql_ms": 2.538, "fetch_ms": 0, "django_ms": 14.859, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_product / 0f2bb9c2": 1, "dojo_engagement / 36b4f668": 1, "dojo_engagement / b1786b70": 1, "dojo_notes / 3da31464": 1, "dojo_risk_acceptance / e11b6d2a": 1, "dojo_fileupload / 12cce93d": 1, "dojo_tagulous_engagement_tags / fdc485d6": 1}, "bytes": 17336, "rows": 20}
### engagements_20: dojo_notes / 3da31464, observed 0.53 ms
SELECT <projection> FROM "dojo_notes" INNER JOIN "dojo_engagement_notes" ON ("dojo_notes"."id" = "dojo_engagement_notes"."notes_id") LEFT OUTER JOIN "dojo_note_type" ON ("dojo_notes"."note_type_id" = "dojo_note_type"."id") INNER JOIN "auth_user" ON ("dojo_notes"."author_id" = "auth_user"."id") LEFT OUTER JOIN "auth_user" T6 ON ("dojo_notes"."editor_id" = T6."id") WHERE "dojo_engagement_notes"."engagement_id" IN (<parameters>) ORDER BY "dojo_notes"."date" DESC
Sort  (cost=73.07..73.58 rows=204 width=4247) (actual rows=0.00 loops=1)
  Sort Key: dojo_notes.date DESC
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=2
  ->  Hash Left Join  (cost=50.01..65.25 rows=204 width=4247) (actual rows=0.00 loops=1)
        Hash Cond: (dojo_notes.editor_id = t6.id)
        Buffers: shared hit=2
        ->  Hash Join  (cost=48.92..63.61 rows=204 width=2480) (actual rows=0.00 loops=1)
              Hash Cond: (dojo_notes.author_id = auth_user.id)
              Buffers: shared hit=2
              ->  Hash Left Join  (cost=47.83..61.98 rows=204 width=713) (actual rows=0.00 loops=1)
                    Hash Cond: (dojo_notes.note_type_id = dojo_note_type.id)
                    Buffers: shared hit=1
                    ->  Hash Join  (cost=35.13..48.73 rows=204 width=70) (actual rows=0.00 loops=1)
                          Hash Cond: (dojo_engagement_notes.notes_id = dojo_notes.id)
                          Buffers: shared hit=1
                          ->  Bitmap Heap Scan on dojo_engagement_notes  (cost=5.78..18.84 rows=204 width=8) (actual rows=0.00 loops=1)
                                Recheck Cond: (engagement_id = ANY ('?'::integer[]))
                                Buffers: shared hit=1
                                ->  Bitmap Index Scan on dojo_engagement_notes_engagement_id_6d165427  (cost=0.00..5.68 rows=204 width=0) (actual rows=0.00 loops=1)
                                      Index Cond: (engagement_id = ANY ('?'::integer[]))
                                      Index Searches: 1
                                      Buffers: shared hit=1
                          ->  Hash  (cost=18.60..18.60 rows=860 width=66) (never executed)
                                ->  Seq Scan on dojo_notes  (cost=0.00..18.60 rows=860 width=66) (never executed)
                    ->  Hash  (cost=11.20..11.20 rows=120 width=643) (never executed)
                          ->  Seq Scan on dojo_note_type  (cost=0.00..11.20 rows=120 width=643) (never executed)
              ->  Hash  (cost=1.04..1.04 rows=4 width=1767) (actual rows=1.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 9kB
                    Buffers: shared hit=1
                    ->  Seq Scan on auth_user  (cost=0.00..1.04 rows=4 width=1767) (actual rows=1.00 loops=1)
                          Buffers: shared hit=1
        ->  Hash  (cost=1.04..1.04 rows=4 width=1767) (never executed)
              ->  Seq Scan on auth_user t6  (cost=0.00..1.04 rows=4 width=1767) (never executed)
Planning Time: 0.243 ms
Execution Time: 0.075 ms
### engagements_20: dojo_engagement / 36b4f668, observed 0.43 ms
SELECT <projection> FROM (SELECT DISTINCT "dojo_engagement"."id" AS "col1", "dojo_engagement"."created" AS "col2", "dojo_engagement"."updated" AS "col3", "dojo_engagement"."name" AS "col4", "dojo_engagement"."description" AS "col5", "dojo_engagement"."version" AS "col6", "dojo_engagement"."first_contacted" AS "col7", "dojo_engagement"."target_start" AS "col8", "dojo_engagement"."target_end" AS "col9", "dojo_engagement"."lead_id" AS "col10", "dojo_engagement"."requester_id" AS "col11", "dojo_engagement"."preset_id" AS "col12", "dojo_engagement"."reason" AS "col13", "dojo_engagement"."report_type_id" AS "col14", "dojo_engagement"."product_id" AS "col15", "dojo_engagement"."active" AS "col16", "dojo_engagement"."tracker" AS "col17", "dojo_engagement"."test_strategy" AS "col18", "dojo_engagement"."threat_model" AS "col19", "dojo_engagement"."api_test" AS "col20", "dojo_engagement"."pen_test" AS "col21", "dojo_engagement"."check_list" AS "col22", "dojo_engagement"."status" AS "col23", "dojo_engagement"."progress" AS "col24", "dojo_engagement"."tmodel_path" AS "col25", "dojo_engagement"."done_testing" AS "col26", "dojo_engagement"."engagement_type" AS "col27", "dojo_engagement"."build_id" AS "col28", "dojo_engagement"."commit_hash" AS "col29", "dojo_engagement"."branch_tag" AS "col30", "dojo_engagement"."source_code_management_uri" AS "col31", "dojo_engagement"."cicd_scm_server_id" A
Aggregate  (cost=2.14..2.15 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=2
  ->  Unique  (cost=2.03..2.13 rows=1 width=5495) (actual rows=100.00 loops=1)
        Buffers: shared hit=2
        ->  Sort  (cost=2.03..2.04 rows=1 width=5495) (actual rows=100.00 loops=1)
              Sort Key: dojo_engagement.id, dojo_engagement.created, dojo_engagement.updated, dojo_engagement.name, dojo_engagement.description, dojo_engagement.version, dojo_engagement.first_contacted, dojo_engagement.target_start, dojo_engagement.target_end, dojo_engagement.lead_id, dojo_engagement.requester_id, dojo_engagement.preset_id, dojo_engagement.reason, dojo_engagement.report_type_id, dojo_engagement.active, dojo_engagement.tracker, dojo_engagement.test_strategy, dojo_engagement.threat_model, dojo_engagement.api_test, dojo_engagement.pen_test, dojo_engagement.check_list, dojo_engagement.status, dojo_engagement.progress, dojo_engagement.tmodel_path, dojo_engagement.done_testing, dojo_engagement.engagement_type, dojo_engagement.build_id, dojo_engagement.commit_hash, dojo_engagement.branch_tag, dojo_engagement.source_code_management_uri, dojo_engagement.cicd_scm_server_id, dojo_engagement.cicd_build_server_id, dojo_engagement.cicd_orchestration_engine_id, dojo_engagement.deduplication_on_engagement, dojo_engagement.archived_at, dojo_engagement.archive_batch
              Sort Method: quicksort  Memory: 38kB
              Buffers: shared hit=2
              ->  Seq Scan on dojo_engagement  (cost=0.00..2.02 rows=1 width=5495) (actual rows=100.00 loops=1)
                    Filter: (product_id = 9)
                    Buffers: shared hit=2
Planning:
  Buffers: shared hit=1
Planning Time: 0.129 ms
Execution Time: 0.138 ms
{"case": "engagements_100", "url": "/api/v2/engagements/?product=9&limit=100", "status": 200, "sql_count": 10, "sql_ms": 3.534, "fetch_ms": 0, "django_ms": 32.419, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_product / 0f2bb9c2": 1, "dojo_engagement / 36b4f668": 1, "dojo_engagement / e0fccee6": 1, "dojo_notes / d320d33c": 1, "dojo_risk_acceptance / 8d586863": 1, "dojo_fileupload / e5d91dba": 1, "dojo_tagulous_engagement_tags / 32388b4e": 1}, "bytes": 86166, "rows": 100}
### engagements_100: dojo_notes / d320d33c, observed 0.77 ms
SELECT <projection> FROM "dojo_notes" INNER JOIN "dojo_engagement_notes" ON ("dojo_notes"."id" = "dojo_engagement_notes"."notes_id") LEFT OUTER JOIN "dojo_note_type" ON ("dojo_notes"."note_type_id" = "dojo_note_type"."id") INNER JOIN "auth_user" ON ("dojo_notes"."author_id" = "auth_user"."id") LEFT OUTER JOIN "auth_user" T6 ON ("dojo_notes"."editor_id" = T6."id") WHERE "dojo_engagement_notes"."engagement_id" IN (<parameters>) ORDER BY "dojo_notes"."date" DESC
Sort  (cost=2005.70..2008.25 rows=1020 width=4247) (actual rows=0.00 loops=1)
  Sort Key: dojo_notes.date DESC
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=2
  ->  Hash Left Join  (cost=56.54..92.73 rows=1020 width=4247) (actual rows=0.00 loops=1)
        Hash Cond: (dojo_notes.editor_id = t6.id)
        Buffers: shared hit=2
        ->  Hash Join  (cost=55.45..88.90 rows=1020 width=2480) (actual rows=0.00 loops=1)
              Hash Cond: (dojo_notes.author_id = auth_user.id)
              Buffers: shared hit=2
              ->  Hash Left Join  (cost=54.36..85.08 rows=1020 width=713) (actual rows=0.00 loops=1)
                    Hash Cond: (dojo_notes.note_type_id = dojo_note_type.id)
                    Buffers: shared hit=1
                    ->  Hash Join  (cost=41.66..69.65 rows=1020 width=70) (actual rows=0.00 loops=1)
                          Hash Cond: (dojo_engagement_notes.notes_id = dojo_notes.id)
                          Buffers: shared hit=1
                          ->  Bitmap Heap Scan on dojo_engagement_notes  (cost=12.31..37.61 rows=1020 width=8) (actual rows=0.00 loops=1)
                                Recheck Cond: (engagement_id = ANY ('?'::integer[]))
                                Buffers: shared hit=1
                                ->  Bitmap Index Scan on dojo_engagement_notes_engagement_id_6d165427  (cost=0.00..11.80 rows=1020 width=0) (actual rows=0.00 loops=1)
                                      Index Cond: (engagement_id = ANY ('?'::integer[]))
                                      Index Searches: 1
                                      Buffers: shared hit=1
                          ->  Hash  (cost=18.60..18.60 rows=860 width=66) (never executed)
                                ->  Seq Scan on dojo_notes  (cost=0.00..18.60 rows=860 width=66) (never executed)
                    ->  Hash  (cost=11.20..11.20 rows=120 width=643) (never executed)
                          ->  Seq Scan on dojo_note_type  (cost=0.00..11.20 rows=120 width=643) (never executed)
              ->  Hash  (cost=1.04..1.04 rows=4 width=1767) (actual rows=1.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 9kB
                    Buffers: shared hit=1
                    ->  Seq Scan on auth_user  (cost=0.00..1.04 rows=4 width=1767) (actual rows=1.00 loops=1)
                          Buffers: shared hit=1
        ->  Hash  (cost=1.04..1.04 rows=4 width=1767) (never executed)
              ->  Seq Scan on auth_user t6  (cost=0.00..1.04 rows=4 width=1767) (never executed)
Planning Time: 0.374 ms
Execution Time: 0.102 ms
### engagements_100: dojo_engagement / e0fccee6, observed 0.48 ms
SELECT <projection> FROM "dojo_engagement" WHERE "dojo_engagement"."product_id" = %s ORDER BY "dojo_engagement"."id" ASC LIMIT 100
Limit  (cost=2.03..2.13 rows=1 width=5495) (actual rows=100.00 loops=1)
  Buffers: shared hit=2
  ->  Unique  (cost=2.03..2.13 rows=1 width=5495) (actual rows=100.00 loops=1)
        Buffers: shared hit=2
        ->  Sort  (cost=2.03..2.04 rows=1 width=5495) (actual rows=100.00 loops=1)
              Sort Key: id, created, updated, name, description, version, first_contacted, target_start, target_end, lead_id, requester_id, preset_id, reason, report_type_id, active, tracker, test_strategy, threat_model, api_test, pen_test, check_list, status, progress, tmodel_path, done_testing, engagement_type, build_id, commit_hash, branch_tag, source_code_management_uri, cicd_scm_server_id, cicd_build_server_id, cicd_orchestration_engine_id, deduplication_on_engagement, archived_at, archive_batch
              Sort Method: quicksort  Memory: 38kB
              Buffers: shared hit=2
              ->  Seq Scan on dojo_engagement  (cost=0.00..2.02 rows=1 width=5495) (actual rows=100.00 loops=1)
                    Filter: (product_id = 9)
                    Buffers: shared hit=2
Planning:
  Buffers: shared hit=1
Planning Time: 0.111 ms
Execution Time: 0.150 ms
### engagements_100: dojo_engagement / 36b4f668, observed 0.45 ms
SELECT <projection> FROM (SELECT DISTINCT "dojo_engagement"."id" AS "col1", "dojo_engagement"."created" AS "col2", "dojo_engagement"."updated" AS "col3", "dojo_engagement"."name" AS "col4", "dojo_engagement"."description" AS "col5", "dojo_engagement"."version" AS "col6", "dojo_engagement"."first_contacted" AS "col7", "dojo_engagement"."target_start" AS "col8", "dojo_engagement"."target_end" AS "col9", "dojo_engagement"."lead_id" AS "col10", "dojo_engagement"."requester_id" AS "col11", "dojo_engagement"."preset_id" AS "col12", "dojo_engagement"."reason" AS "col13", "dojo_engagement"."report_type_id" AS "col14", "dojo_engagement"."product_id" AS "col15", "dojo_engagement"."active" AS "col16", "dojo_engagement"."tracker" AS "col17", "dojo_engagement"."test_strategy" AS "col18", "dojo_engagement"."threat_model" AS "col19", "dojo_engagement"."api_test" AS "col20", "dojo_engagement"."pen_test" AS "col21", "dojo_engagement"."check_list" AS "col22", "dojo_engagement"."status" AS "col23", "dojo_engagement"."progress" AS "col24", "dojo_engagement"."tmodel_path" AS "col25", "dojo_engagement"."done_testing" AS "col26", "dojo_engagement"."engagement_type" AS "col27", "dojo_engagement"."build_id" AS "col28", "dojo_engagement"."commit_hash" AS "col29", "dojo_engagement"."branch_tag" AS "col30", "dojo_engagement"."source_code_management_uri" AS "col31", "dojo_engagement"."cicd_scm_server_id" A
Aggregate  (cost=2.14..2.15 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=2
  ->  Unique  (cost=2.03..2.13 rows=1 width=5495) (actual rows=100.00 loops=1)
        Buffers: shared hit=2
        ->  Sort  (cost=2.03..2.04 rows=1 width=5495) (actual rows=100.00 loops=1)
              Sort Key: dojo_engagement.id, dojo_engagement.created, dojo_engagement.updated, dojo_engagement.name, dojo_engagement.description, dojo_engagement.version, dojo_engagement.first_contacted, dojo_engagement.target_start, dojo_engagement.target_end, dojo_engagement.lead_id, dojo_engagement.requester_id, dojo_engagement.preset_id, dojo_engagement.reason, dojo_engagement.report_type_id, dojo_engagement.active, dojo_engagement.tracker, dojo_engagement.test_strategy, dojo_engagement.threat_model, dojo_engagement.api_test, dojo_engagement.pen_test, dojo_engagement.check_list, dojo_engagement.status, dojo_engagement.progress, dojo_engagement.tmodel_path, dojo_engagement.done_testing, dojo_engagement.engagement_type, dojo_engagement.build_id, dojo_engagement.commit_hash, dojo_engagement.branch_tag, dojo_engagement.source_code_management_uri, dojo_engagement.cicd_scm_server_id, dojo_engagement.cicd_build_server_id, dojo_engagement.cicd_orchestration_engine_id, dojo_engagement.deduplication_on_engagement, dojo_engagement.archived_at, dojo_engagement.archive_batch
              Sort Method: quicksort  Memory: 38kB
              Buffers: shared hit=2
              ->  Seq Scan on dojo_engagement  (cost=0.00..2.02 rows=1 width=5495) (actual rows=100.00 loops=1)
                    Filter: (product_id = 9)
                    Buffers: shared hit=2
Planning:
  Buffers: shared hit=1
Planning Time: 0.111 ms
Execution Time: 0.133 ms
{"case": "engagement_detail", "url": "/api/v2/engagements/13/", "status": 200, "sql_count": 8, "sql_ms": 1.793, "fetch_ms": 0, "django_ms": 8.862, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_engagement / 343b5f2b": 1, "dojo_notes / c8142c5a": 1, "dojo_risk_acceptance / eb993df3": 1, "dojo_fileupload / 396fcebb": 1, "dojo_tagulous_engagement_tags / 55e9f977": 1}, "bytes": 860, "rows": 1}
### engagement_detail: dojo_notes / c8142c5a, observed 0.50 ms
SELECT <projection> FROM "dojo_notes" INNER JOIN "dojo_engagement_notes" ON ("dojo_notes"."id" = "dojo_engagement_notes"."notes_id") LEFT OUTER JOIN "dojo_note_type" ON ("dojo_notes"."note_type_id" = "dojo_note_type"."id") INNER JOIN "auth_user" ON ("dojo_notes"."author_id" = "auth_user"."id") LEFT OUTER JOIN "auth_user" T6 ON ("dojo_notes"."editor_id" = T6."id") WHERE "dojo_engagement_notes"."engagement_id" IN (%s) ORDER BY "dojo_notes"."date" DESC
Sort  (cost=40.34..40.36 rows=10 width=4247) (actual rows=0.00 loops=1)
  Sort Key: dojo_notes.date DESC
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=2
  ->  Hash Left Join  (cost=17.23..40.17 rows=10 width=4247) (actual rows=0.00 loops=1)
        Hash Cond: (dojo_notes.editor_id = t6.id)
        Buffers: shared hit=2
        ->  Hash Join  (cost=16.14..39.05 rows=10 width=2480) (actual rows=0.00 loops=1)
              Hash Cond: (dojo_notes.author_id = auth_user.id)
              Buffers: shared hit=2
              ->  Nested Loop Left Join  (cost=15.05..37.94 rows=10 width=713) (actual rows=0.00 loops=1)
                    Buffers: shared hit=1
                    ->  Hash Join  (cost=14.91..35.78 rows=10 width=70) (actual rows=0.00 loops=1)
                          Hash Cond: (dojo_notes.id = dojo_engagement_notes.notes_id)
                          Buffers: shared hit=1
                          ->  Seq Scan on dojo_notes  (cost=0.00..18.60 rows=860 width=66) (actual rows=0.00 loops=1)
                                Buffers: shared hit=1
                          ->  Hash  (cost=14.79..14.79 rows=10 width=8) (never executed)
                                ->  Bitmap Heap Scan on dojo_engagement_notes  (cost=4.23..14.79 rows=10 width=8) (never executed)
                                      Recheck Cond: (engagement_id = 13)
                                      ->  Bitmap Index Scan on dojo_engagement_notes_engagement_id_6d165427  (cost=0.00..4.23 rows=10 width=0) (never executed)
                                            Index Cond: (engagement_id = 13)
                                            Index Searches: 0
                    ->  Index Scan using dojo_note_type_pkey on dojo_note_type  (cost=0.14..0.22 rows=1 width=643) (never executed)
                          Index Cond: (id = dojo_notes.note_type_id)
                          Index Searches: 0
              ->  Hash  (cost=1.04..1.04 rows=4 width=1767) (actual rows=1.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 9kB
                    Buffers: shared hit=1
                    ->  Seq Scan on auth_user  (cost=0.00..1.04 rows=4 width=1767) (actual rows=1.00 loops=1)
                          Buffers: shared hit=1
        ->  Hash  (cost=1.04..1.04 rows=4 width=1767) (never executed)
              ->  Seq Scan on auth_user t6  (cost=0.00..1.04 rows=4 width=1767) (never executed)
Planning Time: 0.270 ms
Execution Time: 0.052 ms
{"case": "engagements_filtered", "url": "/api/v2/engagements/?product=9&product__tags__and=round2,perf-fixture&not_tags=excluded&o=-name&limit=100", "status": 200, "sql_count": 10, "sql_ms": 5.858, "fetch_ms": 0, "django_ms": 37.053, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_product / 0f2bb9c2": 1, "dojo_engagement / 23e84c1f": 1, "dojo_engagement / 93602962": 1, "dojo_notes / d320d33c": 1, "dojo_risk_acceptance / 8d586863": 1, "dojo_fileupload / e5d91dba": 1, "dojo_tagulous_engagement_tags / 32388b4e": 1}, "bytes": 86166, "rows": 100}
### engagements_filtered: dojo_engagement / 23e84c1f, observed 1.66 ms
SELECT <projection> FROM (SELECT DISTINCT "dojo_engagement"."id" AS "col1", "dojo_engagement"."created" AS "col2", "dojo_engagement"."updated" AS "col3", "dojo_engagement"."name" AS "col4", "dojo_engagement"."description" AS "col5", "dojo_engagement"."version" AS "col6", "dojo_engagement"."first_contacted" AS "col7", "dojo_engagement"."target_start" AS "col8", "dojo_engagement"."target_end" AS "col9", "dojo_engagement"."lead_id" AS "col10", "dojo_engagement"."requester_id" AS "col11", "dojo_engagement"."preset_id" AS "col12", "dojo_engagement"."reason" AS "col13", "dojo_engagement"."report_type_id" AS "col14", "dojo_engagement"."product_id" AS "col15", "dojo_engagement"."active" AS "col16", "dojo_engagement"."tracker" AS "col17", "dojo_engagement"."test_strategy" AS "col18", "dojo_engagement"."threat_model" AS "col19", "dojo_engagement"."api_test" AS "col20", "dojo_engagement"."pen_test" AS "col21", "dojo_engagement"."check_list" AS "col22", "dojo_engagement"."status" AS "col23", "dojo_engagement"."progress" AS "col24", "dojo_engagement"."tmodel_path" AS "col25", "dojo_engagement"."done_testing" AS "col26", "dojo_engagement"."engagement_type" AS "col27", "dojo_engagement"."build_id" AS "col28", "dojo_engagement"."commit_hash" AS "col29", "dojo_engagement"."branch_tag" AS "col30", "dojo_engagement"."source_code_management_uri" AS "col31", "dojo_engagement"."cicd_scm_server_id" A
Aggregate  (cost=24.48..24.49 rows=1 width=8) (actual rows=1.00 loops=1)
  Buffers: shared hit=602
  ->  Unique  (cost=24.24..24.47 rows=1 width=5503) (actual rows=100.00 loops=1)
        Buffers: shared hit=602
        ->  Incremental Sort  (cost=24.24..24.29 rows=2 width=5503) (actual rows=100.00 loops=1)
              Sort Key: dojo_engagement.id, dojo_engagement.created, dojo_engagement.updated, dojo_engagement.name, dojo_engagement.description, dojo_engagement.version, dojo_engagement.first_contacted, dojo_engagement.target_start, dojo_engagement.target_end, dojo_engagement.lead_id, dojo_engagement.requester_id, dojo_engagement.preset_id, dojo_engagement.reason, dojo_engagement.report_type_id, dojo_engagement.active, dojo_engagement.tracker, dojo_engagement.test_strategy, dojo_engagement.threat_model, dojo_engagement.api_test, dojo_engagement.pen_test, dojo_engagement.check_list, dojo_engagement.status, dojo_engagement.progress, dojo_engagement.tmodel_path, dojo_engagement.done_testing, dojo_engagement.engagement_type, dojo_engagement.build_id, dojo_engagement.commit_hash, dojo_engagement.branch_tag, dojo_engagement.source_code_management_uri, dojo_engagement.cicd_scm_server_id, dojo_engagement.cicd_build_server_id, dojo_engagement.cicd_orchestration_engine_id, dojo_engagement.deduplication_on_engagement, dojo_engagement.archived_at, dojo_engagement.archive_batch, (count(dojo_tagulous_product_tags.name))
              Presorted Key: dojo_engagement.id
              Full-sort Groups: 4  Sort Method: quicksort  Average Memory: 29kB  Peak Memory: 29kB
              Buffers: shared hit=602
              ->  GroupAggregate  (cost=24.21..24.23 rows=1 width=5503) (actual rows=100.00 loops=1)
                    Group Key: dojo_engagement.id
                    Filter: (count(dojo_tagulous_product_tags.name) = 2)
                    Buffers: shared hit=602
                    ->  Sort  (cost=24.21..24.21 rows=1 width=6011) (actual rows=200.00 loops=1)
                          Sort Key: dojo_engagement.id
                          Sort Method: quicksort  Memory: 53kB
                          Buffers: shared hit=602
                          ->  Nested Loop  (cost=0.30..24.20 rows=1 width=6011) (actual rows=200.00 loops=1)
                                Join Filter: (dojo_product_tags.tagulous_product_tags_id = dojo_tagulous_product_tags.id)
                                Rows Removed by Join Filter: 100
                                Buffers: shared hit=602
                                ->  Nested Loop  (cost=0.30..23.02 rows=1 width=5499) (actual rows=200.00 loops=1)
                                      Buffers: shared hit=402
                                      ->  Nested Loop  (cost=0.30..19.46 rows=1 width=5499) (actual rows=100.00 loops=1)
                                            Buffers: shared hit=302
                                            ->  Nested Loop Anti Join  (cost=0.30..18.38 rows=1 width=5495) (actual rows=100.00 loops=1)
                                                  Buffers: shared hit=202
                                                  ->  Seq Scan on dojo_engagement  (cost=0.00..2.02 rows=1 width=5495) (actual rows=100.00 loops=1)
                                                        Filter: (product_id = 9)
                                                        Buffers: shared hit=2
                                                  ->  Nested Loop  (cost=0.30..16.34 rows=1 width=4) (actual rows=0.00 loops=100)
                                                        Buffers: shared hit=200
                                                        ->  Index Scan using dojo_tagulous_engagement_tags_name_31be1c2f_like on dojo_tagulous_engagement_tags u2  (cost=0.14..8.16 rows=1 width=4) (actual rows=0.00 loops=100)
                                                              Index Cond: ((name)::text = '?'::text)
                                                              Index Searches: 100
                                                              Buffers: shared hit=200
                                                        ->  Index Only Scan using dojo_engagement_tags_engagement_id_tagulous_e_da1b8224_uniq on dojo_engagement_tags u1  (cost=0.15..8.17 rows=1 width=8) (never executed)
                                                              Index Cond: ((engagement_id = dojo_engagement.id) AND (tagulous_engagement_tags_id = u2.id))
                                                              Heap Fetches: 0
                                                              Index Searches: 0
                                            ->  Seq Scan on dojo_product  (cost=0.00..1.07 rows=1 width=4) (actual rows=1.00 loops=100)
                                                  Filter: (id = 9)
                                                  Buffers: shared hit=100
                                      ->  Seq Scan on dojo_product_tags  (cost=0.00..3.55 rows=1 width=8) (actual rows=2.00 loops=100)
                                            Filter: (product_id = 9)
                                            Buffers: shared hit=100
                                ->  Seq Scan on dojo_tagulous_product_tags  (cost=0.00..1.15 rows=2 width=520) (actual rows=1.50 loops=200)
                                      Filter: ((name)::text = ANY ('?'::text[]))
                                      Buffers: shared hit=200
Planning:
  Buffers: shared hit=12
Planning Time: 0.502 ms
Execution Time: 0.750 ms
### engagements_filtered: dojo_engagement / 93602962, observed 1.51 ms
SELECT <projection> FROM "dojo_engagement" INNER JOIN "dojo_product" ON ("dojo_engagement"."product_id" = "dojo_product"."id") INNER JOIN "dojo_product_tags" ON ("dojo_product"."id" = "dojo_product_tags"."product_id") INNER JOIN "dojo_tagulous_product_tags" ON ("dojo_product_tags"."tagulous_product_tags_id" = "dojo_tagulous_product_tags"."id") WHERE ("dojo_engagement"."product_id" = %s AND "dojo_tagulous_product_tags"."name" IN (%s, %s) AND NOT (EXISTS(SELECT %s AS "a" FROM "dojo_engagement_tags" U1 INNER JOIN "dojo_tagulous_engagement_tags" U2 ON (U1."tagulous_engagement_tags_id" = U2."id") WHERE (U2."name" IN (%s) AND U1."engagement_id" = ("dojo_engagement"."id")) LIMIT 1))) GROUP BY "dojo_engagement"."id" HAVING COUNT("dojo_tagulous_product_tags"."name") = %s ORDER BY "dojo_engagement"."name" DESC LIMIT 100
Limit  (cost=24.24..24.34 rows=1 width=5503) (actual rows=100.00 loops=1)
  Buffers: shared hit=602
  ->  Unique  (cost=24.24..24.34 rows=1 width=5503) (actual rows=100.00 loops=1)
        Buffers: shared hit=602
        ->  Sort  (cost=24.24..24.25 rows=1 width=5503) (actual rows=100.00 loops=1)
              Sort Key: dojo_engagement.name DESC, dojo_engagement.id, dojo_engagement.created, dojo_engagement.updated, dojo_engagement.description, dojo_engagement.version, dojo_engagement.first_contacted, dojo_engagement.target_start, dojo_engagement.target_end, dojo_engagement.lead_id, dojo_engagement.requester_id, dojo_engagement.preset_id, dojo_engagement.reason, dojo_engagement.report_type_id, dojo_engagement.active, dojo_engagement.tracker, dojo_engagement.test_strategy, dojo_engagement.threat_model, dojo_engagement.api_test, dojo_engagement.pen_test, dojo_engagement.check_list, dojo_engagement.status, dojo_engagement.progress, dojo_engagement.tmodel_path, dojo_engagement.done_testing, dojo_engagement.engagement_type, dojo_engagement.build_id, dojo_engagement.commit_hash, dojo_engagement.branch_tag, dojo_engagement.source_code_management_uri, dojo_engagement.cicd_scm_server_id, dojo_engagement.cicd_build_server_id, dojo_engagement.cicd_orchestration_engine_id, dojo_engagement.deduplication_on_engagement, dojo_engagement.archived_at, dojo_engagement.archive_batch, (count(dojo_tagulous_product_tags.name))
              Sort Method: quicksort  Memory: 39kB
              Buffers: shared hit=602
              ->  GroupAggregate  (cost=24.21..24.23 rows=1 width=5503) (actual rows=100.00 loops=1)
                    Group Key: dojo_engagement.id
                    Filter: (count(dojo_tagulous_product_tags.name) = 2)
                    Buffers: shared hit=602
                    ->  Sort  (cost=24.21..24.21 rows=1 width=6011) (actual rows=200.00 loops=1)
                          Sort Key: dojo_engagement.id
                          Sort Method: quicksort  Memory: 53kB
                          Buffers: shared hit=602
                          ->  Nested Loop  (cost=0.30..24.20 rows=1 width=6011) (actual rows=200.00 loops=1)
                                Join Filter: (dojo_product_tags.tagulous_product_tags_id = dojo_tagulous_product_tags.id)
                                Rows Removed by Join Filter: 100
                                Buffers: shared hit=602
                                ->  Nested Loop  (cost=0.30..23.02 rows=1 width=5499) (actual rows=200.00 loops=1)
                                      Buffers: shared hit=402
                                      ->  Nested Loop  (cost=0.30..19.46 rows=1 width=5499) (actual rows=100.00 loops=1)
                                            Buffers: shared hit=302
                                            ->  Nested Loop Anti Join  (cost=0.30..18.38 rows=1 width=5495) (actual rows=100.00 loops=1)
                                                  Buffers: shared hit=202
                                                  ->  Seq Scan on dojo_engagement  (cost=0.00..2.02 rows=1 width=5495) (actual rows=100.00 loops=1)
                                                        Filter: (product_id = 9)
                                                        Buffers: shared hit=2
                                                  ->  Nested Loop  (cost=0.30..16.34 rows=1 width=4) (actual rows=0.00 loops=100)
                                                        Buffers: shared hit=200
                                                        ->  Index Scan using dojo_tagulous_engagement_tags_name_31be1c2f_like on dojo_tagulous_engagement_tags u2  (cost=0.14..8.16 rows=1 width=4) (actual rows=0.00 loops=100)
                                                              Index Cond: ((name)::text = '?'::text)
                                                              Index Searches: 100
                                                              Buffers: shared hit=200
                                                        ->  Index Only Scan using dojo_engagement_tags_engagement_id_tagulous_e_da1b8224_uniq on dojo_engagement_tags u1  (cost=0.15..8.17 rows=1 width=8) (never executed)
                                                              Index Cond: ((engagement_id = dojo_engagement.id) AND (tagulous_engagement_tags_id = u2.id))
                                                              Heap Fetches: 0
                                                              Index Searches: 0
                                            ->  Seq Scan on dojo_product  (cost=0.00..1.07 rows=1 width=4) (actual rows=1.00 loops=100)
                                                  Filter: (id = 9)
                                                  Buffers: shared hit=100
                                      ->  Seq Scan on dojo_product_tags  (cost=0.00..3.55 rows=1 width=8) (actual rows=2.00 loops=100)
                                            Filter: (product_id = 9)
                                            Buffers: shared hit=100
                                ->  Seq Scan on dojo_tagulous_product_tags  (cost=0.00..1.15 rows=2 width=520) (actual rows=1.50 loops=200)
                                      Filter: ((name)::text = ANY ('?'::text[]))
                                      Buffers: shared hit=200
Planning:
  Buffers: shared hit=12
Planning Time: 0.425 ms
Execution Time: 0.745 ms
### engagements_filtered: dojo_notes / d320d33c, observed 0.67 ms
SELECT <projection> FROM "dojo_notes" INNER JOIN "dojo_engagement_notes" ON ("dojo_notes"."id" = "dojo_engagement_notes"."notes_id") LEFT OUTER JOIN "dojo_note_type" ON ("dojo_notes"."note_type_id" = "dojo_note_type"."id") INNER JOIN "auth_user" ON ("dojo_notes"."author_id" = "auth_user"."id") LEFT OUTER JOIN "auth_user" T6 ON ("dojo_notes"."editor_id" = T6."id") WHERE "dojo_engagement_notes"."engagement_id" IN (<parameters>) ORDER BY "dojo_notes"."date" DESC
Sort  (cost=2005.70..2008.25 rows=1020 width=4247) (actual rows=0.00 loops=1)
  Sort Key: dojo_notes.date DESC
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=2
  ->  Hash Left Join  (cost=56.54..92.73 rows=1020 width=4247) (actual rows=0.00 loops=1)
        Hash Cond: (dojo_notes.editor_id = t6.id)
        Buffers: shared hit=2
        ->  Hash Join  (cost=55.45..88.90 rows=1020 width=2480) (actual rows=0.00 loops=1)
              Hash Cond: (dojo_notes.author_id = auth_user.id)
              Buffers: shared hit=2
              ->  Hash Left Join  (cost=54.36..85.08 rows=1020 width=713) (actual rows=0.00 loops=1)
                    Hash Cond: (dojo_notes.note_type_id = dojo_note_type.id)
                    Buffers: shared hit=1
                    ->  Hash Join  (cost=41.66..69.65 rows=1020 width=70) (actual rows=0.00 loops=1)
                          Hash Cond: (dojo_engagement_notes.notes_id = dojo_notes.id)
                          Buffers: shared hit=1
                          ->  Bitmap Heap Scan on dojo_engagement_notes  (cost=12.31..37.61 rows=1020 width=8) (actual rows=0.00 loops=1)
                                Recheck Cond: (engagement_id = ANY ('?'::integer[]))
                                Buffers: shared hit=1
                                ->  Bitmap Index Scan on dojo_engagement_notes_engagement_id_6d165427  (cost=0.00..11.80 rows=1020 width=0) (actual rows=0.00 loops=1)
                                      Index Cond: (engagement_id = ANY ('?'::integer[]))
                                      Index Searches: 1
                                      Buffers: shared hit=1
                          ->  Hash  (cost=18.60..18.60 rows=860 width=66) (never executed)
                                ->  Seq Scan on dojo_notes  (cost=0.00..18.60 rows=860 width=66) (never executed)
                    ->  Hash  (cost=11.20..11.20 rows=120 width=643) (never executed)
                          ->  Seq Scan on dojo_note_type  (cost=0.00..11.20 rows=120 width=643) (never executed)
              ->  Hash  (cost=1.04..1.04 rows=4 width=1767) (actual rows=1.00 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 9kB
                    Buffers: shared hit=1
                    ->  Seq Scan on auth_user  (cost=0.00..1.04 rows=4 width=1767) (actual rows=1.00 loops=1)
                          Buffers: shared hit=1
        ->  Hash  (cost=1.04..1.04 rows=4 width=1767) (never executed)
              ->  Seq Scan on auth_user t6  (cost=0.00..1.04 rows=4 width=1767) (never executed)
Planning Time: 0.264 ms
Execution Time: 0.060 ms
{"case": "test_jira_detail", "url": "/api/v2/tests/98/", "status": 200, "sql_count": 209, "sql_ms": 23.98, "fetch_ms": 0, "django_ms": 98.434, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_test / 158c5a93": 1, "dojo_notes / 62704bb0": 1, "dojo_fileupload / 64b43434": 1, "dojo_tagulous_test_tags / 87c84f78": 1, "dojo_finding_group / 370c05b6": 1, "dojo_jira_issue / b4a208b0": 1, "dojo_jira_project / 728c42ef": 100, "dojo_jira_instance / 81ac206d": 100}, "bytes": 31193, "rows": 1}
### test_jira_detail: dojo_jira_issue / b4a208b0, observed 0.37 ms
SELECT <projection> FROM "dojo_jira_issue" WHERE "dojo_jira_issue"."finding_group_id" IN (<parameters>)
Seq Scan on dojo_jira_issue  (cost=0.25..2.49 rows=16 width=896) (actual rows=100.00 loops=1)
  Filter: (finding_group_id = ANY ('?'::integer[]))
  Rows Removed by Filter: 99
  Buffers: shared hit=2
Planning:
  Buffers: shared hit=1
Planning Time: 0.065 ms
Execution Time: 0.043 ms
### test_jira_detail: dojo_jira_project / 728c42ef, observed 0.15 ms
SELECT <projection> FROM "dojo_jira_project" WHERE "dojo_jira_project"."id" = %s LIMIT 21
Limit  (cost=0.14..8.15 rows=1 width=2477) (actual rows=1.00 loops=1)
  Buffers: shared hit=2
  ->  Index Scan using dojo_jira_pkey_pkey on dojo_jira_project  (cost=0.14..8.15 rows=1 width=2477) (actual rows=1.00 loops=1)
        Index Cond: (id = 4)
        Index Searches: 1
        Buffers: shared hit=2
Planning Time: 0.022 ms
Execution Time: 0.025 ms
### test_jira_detail: dojo_jira_instance / 81ac206d, observed 0.13 ms
SELECT <projection> FROM "dojo_jira_instance" WHERE "dojo_jira_instance"."id" = %s LIMIT 21
Limit  (cost=0.14..8.15 rows=1 width=6268) (actual rows=1.00 loops=1)
  Buffers: shared hit=2
  ->  Index Scan using dojo_jira_conf_pkey on dojo_jira_instance  (cost=0.14..8.15 rows=1 width=6268) (actual rows=1.00 loops=1)
        Index Cond: (id = 5)
        Index Searches: 1
        Buffers: shared hit=2
Planning Time: 0.015 ms
Execution Time: 0.015 ms
{"case": "tests_jira_100", "url": "/api/v2/tests/?limit=100", "status": 200, "sql_count": 408, "sql_ms": 48.309, "fetch_ms": 0, "django_ms": 217.965, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_test / 34915665": 1, "dojo_test / f651efd0": 1, "dojo_notes / 554c4b2c": 1, "dojo_fileupload / 510e8c55": 1, "dojo_tagulous_test_tags / 3a7f0429": 1, "dojo_finding_group / 3adc3cc9": 1, "dojo_jira_issue / 885afcb8": 1, "dojo_jira_project / 728c42ef": 199, "dojo_jira_instance / 81ac206d": 199}, "bytes": 124219, "rows": 100}
### tests_jira_100: dojo_jira_project / 728c42ef, observed 0.57 ms
SELECT <projection> FROM "dojo_jira_project" WHERE "dojo_jira_project"."id" = %s LIMIT 21
Limit  (cost=0.14..8.15 rows=1 width=2477) (actual rows=1.00 loops=1)
  Buffers: shared hit=2
  ->  Index Scan using dojo_jira_pkey_pkey on dojo_jira_project  (cost=0.14..8.15 rows=1 width=2477) (actual rows=1.00 loops=1)
        Index Cond: (id = 4)
        Index Searches: 1
        Buffers: shared hit=2
Planning Time: 0.020 ms
Execution Time: 0.134 ms
### tests_jira_100: dojo_jira_issue / 885afcb8, observed 0.56 ms
SELECT <projection> FROM "dojo_jira_issue" WHERE "dojo_jira_issue"."finding_group_id" IN (<parameters>)
Seq Scan on dojo_jira_issue  (cost=0.50..2.74 rows=16 width=896) (actual rows=199.00 loops=1)
  Filter: (finding_group_id = ANY ('?'::integer[]))
  Buffers: shared hit=2
Planning:
  Buffers: shared hit=1
Planning Time: 0.069 ms
Execution Time: 0.043 ms
### tests_jira_100: dojo_jira_instance / 81ac206d, observed 0.23 ms
SELECT <projection> FROM "dojo_jira_instance" WHERE "dojo_jira_instance"."id" = %s LIMIT 21
Limit  (cost=0.14..8.15 rows=1 width=6268) (actual rows=1.00 loops=1)
  Buffers: shared hit=2
  ->  Index Scan using dojo_jira_conf_pkey on dojo_jira_instance  (cost=0.14..8.15 rows=1 width=6268) (actual rows=1.00 loops=1)
        Index Cond: (id = 5)
        Index Searches: 1
        Buffers: shared hit=2
Planning Time: 0.013 ms
Execution Time: 0.013 ms
{"case": "tests_filtered", "url": "/api/v2/tests/?engagement__product__tags__and=round2,perf-fixture&o=title&limit=100", "status": 200, "sql_count": 408, "sql_ms": 56.349, "fetch_ms": 0, "django_ms": 225.341, "queries": {"dojo_system_settings": 1, "authtoken_token": 1, "dojo_usercontactinfo / d589e2dd": 1, "dojo_test / 6d603763": 1, "dojo_test / d00e1807": 1, "dojo_notes / 554c4b2c": 1, "dojo_fileupload / 510e8c55": 1, "dojo_tagulous_test_tags / 3a7f0429": 1, "dojo_finding_group / 3adc3cc9": 1, "dojo_jira_issue / 885afcb8": 1, "dojo_jira_project / 728c42ef": 199, "dojo_jira_instance / 81ac206d": 199}, "bytes": 124219, "rows": 100}
### tests_filtered: dojo_jira_issue / 885afcb8, observed 0.57 ms
SELECT <projection> FROM "dojo_jira_issue" WHERE "dojo_jira_issue"."finding_group_id" IN (<parameters>)
Seq Scan on dojo_jira_issue  (cost=0.50..2.74 rows=16 width=896) (actual rows=199.00 loops=1)
  Filter: (finding_group_id = ANY ('?'::integer[]))
  Buffers: shared hit=2
Planning:
  Buffers: shared hit=1
Planning Time: 0.065 ms
Execution Time: 0.041 ms
### tests_filtered: dojo_jira_project / 728c42ef, observed 0.28 ms
SELECT <projection> FROM "dojo_jira_project" WHERE "dojo_jira_project"."id" = %s LIMIT 21
Limit  (cost=0.14..8.15 rows=1 width=2477) (actual rows=1.00 loops=1)
  Buffers: shared hit=2
  ->  Index Scan using dojo_jira_pkey_pkey on dojo_jira_project  (cost=0.14..8.15 rows=1 width=2477) (actual rows=1.00 loops=1)
        Index Cond: (id = 4)
        Index Searches: 1
        Buffers: shared hit=2
Planning Time: 0.017 ms
Execution Time: 0.019 ms
### tests_filtered: dojo_jira_instance / 81ac206d, observed 0.15 ms
SELECT <projection> FROM "dojo_jira_instance" WHERE "dojo_jira_instance"."id" = %s LIMIT 21
Limit  (cost=0.14..8.15 rows=1 width=6268) (actual rows=1.00 loops=1)
  Buffers: shared hit=2
  ->  Index Scan using dojo_jira_conf_pkey on dojo_jira_instance  (cost=0.14..8.15 rows=1 width=6268) (actual rows=1.00 loops=1)
        Index Cond: (id = 5)
        Index Searches: 1
        Buffers: shared hit=2
Planning Time: 0.013 ms
Execution Time: 0.013 ms
