# Каталог метрик

Общие labels на target: application, cluster, environment, namespace, release, component. У pod есть pod и instance. Пределы указаны на один target без этих labels. Histogram создаёт bucket по каждой границе, +Inf, count и sum. Суммируйте buckets по le и целевым labels перед histogram_quantile.

| Семейство | Тип и единица | Доп. labels и предел | Источник, агрегация и доступность |
|---|---|---|---|
| aspm_http_requests_total | counter, requests | group × method × status | Web, rate и sum по pod. |
| aspm_http_request_duration_seconds | histogram, s | group × method × установленные Django view names | Web, до 17 samples на набор labels. Время до Django response. Fallback unresolved агрегирует маршруты без match. |
| aspm_http_response_bytes | histogram, bytes | group, до 6 | Web, Content-Length или известная длина тела. |
| aspm_http_in_flight | gauge, requests | 1 | Web, livesum и очистка dead process gauges по uWSGI stats. |
| aspm_ingestion_acceptance_seconds | histogram, s | 1 набор | Web, новый ScanRun с HTTP 202. |
| aspm_scan_events_total | counter, transitions | scanner × result, ≤42 | accepted/duplicate/user retry после commit, completed/failed/recovered в worker. |
| aspm_scan_phase_seconds | histogram, s | scanner × stage, ≤42 | Worker, parser, reimport с dedup, snapshot, queue wait, acceptance-to-start/complete успешных scans. |
| aspm_scan_findings_imported_total | counter, Findings | scanner, ≤7 | Worker, новые Findings из результата завершённого импорта. |
| aspm_scan_observations_total | counter, observations | scanner, ≤7 | Worker, число записей опубликованного snapshot после commit. |
| aspm_artifact_bytes | histogram, bytes | format scan/html/json | Web для upload, worker для завершённых артефактов. |
| aspm_report_events_total | counter, events | kind × result, ≤12 | Web/worker, Classic HTML render и generated ASPM lifecycle. |
| aspm_report_phase_seconds | histogram, s | kind × stage, ≤3 | Worker generated generation/queue_wait, web Classic render generation. |
| aspm_storage_failures_total | counter, errors | operation, ≤4 | Worker/web, ошибки операций private evidence. |
| aspm_outbox_dispatch_total | counter, publishes | kind × result, ≤4 | Worker, публикация в broker либо exception. |
| aspm_celery_published_total | counter, publishes | task, ≤4 | Web/worker, after_task_publish. |
| aspm_celery_tasks_total | counter, attempts | task × result, ≤20 | Worker, task_postrun. Celery SUCCESS может включать обработанную ScanRun failure. |
| aspm_celery_task_seconds | histogram, s | task, ≤4 | Worker, task_prerun до postrun. |
| aspm_celery_heartbeat_timestamp_seconds | gauge, Unix s | 1 | Worker heartbeat. Численность учитывает свежесть 20 с. |
| aspm_celery_worker_tasks | gauge, tasks | state active/reserved | Последнее состояние parent Celery. Суммируйте свежие workers. |
| aspm_dependency_up | gauge, 0/1 | source database/broker/storage/security | Beat exporter, отдельный probe на источник. |
| aspm_durable_jobs / aspm_durable_oldest_seconds | gauge, jobs / s | kind × state, ≤3 | Beat exporter, snapshot до 10 001 записей. При больших очередях count и oldest служат нижней границей. |
| aspm_ingestion_outbox_pending | gauge, jobs | 1 | Beat exporter, общий count ограниченной выборки. |
| aspm_broker_queue_ready / aspm_broker_unacked | gauge, broker entries | queue для ready, один unacked на broker keyspace | Beat exporter. Для ready складываются Redis priority lists Kombu. |
| aspm_evidence_filesystem_bytes | gauge, bytes | state total/available | Beat exporter, statvfs и подтверждённый write probe. |
| aspm_postgres_lock_waits | gauge, locks | 1 | Beat exporter, ungranted locks текущей БД/shared objects. |
| aspm_postgres_wal_bytes_total | counter, bytes | 1 | Beat exporter, pg_stat_wal. WAL всего инстанса. |
| aspm_webhook_delivery_attempts_total / aspm_webhook_delivery_duration_seconds / aspm_webhook_events_expanded_total | counter / histogram s | outcome для attempts | Прежние имена. Worker, sum после rate. |
| aspm_webhook_queue_wait_seconds / aspm_webhook_http_total | histogram s / counter | status_class HTTP либо no_response | Worker, первая попытка и ответ HTTP. |
| aspm_webhook_outbox_pending / oldest_seconds / dead / unexpanded | gauge, entries или s | 1 на семью | Beat exporter, bounded SQL при включённых вебхуках. |
| aspm_identity_events_total | counter, events | event × result, ≤6 | Web, фиксированный словарь login/callback/provider/permission/session. |
| aspm_security_projects / repositories / active_findings | gauge, entities | ≤6 severity у Findings | Beat exporter, opt-in, interval ≥300 s и statement_timeout 750 ms. Считаются live Findings. Отправка отдельно opt-in. |

Scanner labels ограничены подтверждённым каталогом. Прочие scanner types относятся к other.

| Инфраструктурный источник | Ряды и агрегация | Предусловия |
|---|---|---|
| PostgreSQL exporter | pg_up, pg_stat_activity_count, pg_stat_activity_max_tx_duration, pg_settings_max_connections, pg_stat_database_xact_commit/rollback/deadlocks/blks_hit/blks_read/temp_bytes, pg_database_size_bytes, pg_locks_count, pg_stat_checkpointer_*, pg_stat_user_tables_autovacuum_count | v0.19.1 на стенде. Группировка по server, datname, state, mode, table. Rate применяется к counters. |
| Redis exporter | redis_up, redis_connected_clients, redis_memory_used_bytes, redis_commands_processed_total, redis_rejected_connections_total, redis_evicted_keys_total | Корпоративный exporter либо v1.81.0. |
| KSM / CSI | kube_deployment_status/spec, kube_pod_container_*, kube_horizontalpodautoscaler_*, kube_poddisruptionbudget_*, kube_job_status_*, kubelet_volume_stats_* | Scope ASPM через namespace и resource labels. Один KSM набор на объект. CSI может не публиковать PVC stats. |
| cAdvisor / node exporter | container_cpu_usage_seconds_total, container_cpu_cfs_*, container_memory_working_set_bytes, node_cpu_seconds_total | Использование по pod/container. Node exporter нужен рядом с внешним хостом PostgreSQL. |
| Traefik | traefik_service_requests_total, traefik_service_request_duration_seconds | Скоуп по Traefik service labels. |
| Prometheus | up, scrape_duration_seconds, scrape_samples_scraped, prometheus_tsdb_*, prometheus_remote_storage_*, process_resident_memory_bytes | По target и remote_name. Lag рассчитывает локальный evaluator. |

Необязательные источники дают NO DATA при отсутствии серий. Reimport и dedup измеряются общей стадией. Группы Keycloak обновляются при повторном входе после TTL. Выделенного refresh polling и RBAC cache hit ratio в кандидате нет.
