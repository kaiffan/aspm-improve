# Операционная диагностика

1. Выберите cluster, environment, namespace и release. Сверьте текущее время и свежесть последней sample.
2. Если панель пуста, сравните Prometheus Targets, локальный query API и query API VictoriaMetrics. Просмотрите lastError до перезапуска pod.
3. При сбое VictoriaMetrics проверьте локальный `prometheus_remote_storage_samples_pending`, ошибки и задержку. Сверьте remote_name, точный URL, egress, сертификат, tenant, auth и WAL. После восстановления запросите исторические samples за интервал сбоя.
4. Для полностью оборванной доставки настройте независимую проверку свежести `up{application="aspm",component="web"}` из сети владельца. Локальный evaluator продолжает оценивать `ASPMRemoteWriteStalled` при доступном Prometheus.
5. Для PostgreSQL сравните число соединений, возраст транзакции, waits и I/O хоста. DBA включает pg_stat_statements и просматривает SQL локально. Используйте отдельную роль с CONNECT и pg_monitor, DSN из Secret и TLS verify-full.
6. Для broker сопоставьте ready, reserved, active и unacked. Часть inventories пересекается. При восстановлении проверьте outbox и результаты ScanRun.
7. Если БД даёт timeout singleton probe, найдите перегрузку или блокировки до изменения cadence. Пустая панель при probe=0 означает отсутствие свежих данных.
8. В Kubernetes сопоставьте Restarts, TerminatedReason и события. Для PVC сравните evidence probe, CSI и квоты. Для OIDC проверьте DNS, CA и состояние IdP отдельно от общего HTTP 403.
