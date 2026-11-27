# 13 | Наблюдаемость

| Слой | Метрика | Первое действие при отклонении |
|---|---|---|
| Ingress | 5xx, TCP/TLS errors, p95/p99, потери соединений | Сопоставить rollout, Ready и EndpointSlice |
| Web | Ready/Startup/Live, rate, p95/p99, CPU throttle и memory | Сопоставить nginx, Django, PostgreSQL и нагрузку на node |
| Worker | Ready/ping, queue age, task failures, task run time | Проверить broker, outbox и длительные задачи |
| Beat / outbox | Наличие одного активного Beat, oldest pending, dispatch retries | Проверить fencing PostgreSQL и попытки публикации |
| PostgreSQL | connections, idle in transaction, waiting locks, WAL, I/O, fsync | DBA сверяет бюджет и активные запросы |
| Storage | Свободные байты/inodes, latency, checksum failures | Проверить CSI, доступность и целостность |
| IdP | Login/callback failures, churn, состояние сертификатов | IAM проверяет issuer, audience, redirect и claims |

Полный [комплект мониторинга](../monitoring/README.md) включает 9 дашбордов, правила и два режима сборщика. Приложение передаёт телеметрию через Prometheus remote_write только на предоставленный URL VictoriaMetrics. Grafana использует существующий источник. JSON импортируются в согласованную папку. Локальные испытания приведены в [VALIDATION](../monitoring/VALIDATION.md).
