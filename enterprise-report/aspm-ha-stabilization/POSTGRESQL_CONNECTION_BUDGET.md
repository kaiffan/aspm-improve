# Бюджет подключений PostgreSQL

Сэмплер записывал `pg_stat_activity` каждые 250 мс в одной выделенной сессии. Считались client backends текущей базы. Сэмплер исключал собственный backend. Отдельные поля содержат активные сеансы, wait event класса Lock и idle in transaction. Это максимум среди измеренных точек. Пики короче интервала могли остаться между замерами. Замер сделан на малом синтетическом датасете и не служит расчётом пропускной способности корпоративного PostgreSQL. [Сырые сэмплы](raw/postgres-samples.jsonl) · [Метки фаз](raw/phase-timestamps.txt) · [Время Job](raw/migration-events.txt) · [Настройки PostgreSQL](raw/postgres-settings.txt)

## Формула профилей

```
W = max(web.replicas, web HPA max при включении)
C = max(worker.replicas, worker HPA max при включении)

W_live = W + web maxSurge + web, ещё живые в Terminating
C_live = C + worker maxSurge + worker, ещё живые в Terminating

per_web = web.processes × web.threads + резерв на pod
per_worker = worker.concurrency + резерв на pod

application = W_live × per_web + C_live × per_worker
              + Beat + migration_jobs + отдельные rollout init sessions
minimum_usable = ceil((application + ops_and_monitors) × 1.25)
max_connections >= minimum_usable + postgres_and_provider_reserved
                   + budget_of_other_databases_and_tenants
```

Штатные `maxSurge=1`, два web-процесса по два потока и два worker child. Для первоначальной оценки выделены 2 дополнительных соединения на web, 1 на worker, 2 на Beat и 2 на Migration Job. Резерв на pod покрывает короткие init/preflight подключения в той же квоте. При параллельном preflight или дополнительных пулах выделите отдельные слоты. Для одного контролируемого rollout расчёт консервативно допускает ещё одну старую генерацию каждого Deployment. При очередном rollout до завершения старых pod это ограничение может быть превышено. Не запускайте параллельные rollout без отдельного расчёта и затухания сессий.

| Профиль | W / C | Верхняя оценка live web / worker | Прикладные сессии | С 10 ops/monitor и запасом 25% | Стартовый серверный лимит для отдельной БД |
|---|---:|---:|---:|---:|---:|
| Standard | 2 / 3 | 5 / 7 | 55 | 82 | 100 |
| High Throughput, web HPA | 3 / 3 | 7 / 7 | 67 | 97 | 120–128 |
| High Throughput, включён и worker HPA | 3 / 4 | 7 / 9 | 73 | 104 | 120–128 |

Серверные лимиты — начальные для выделенной площадки при сверке provider/system reservations и памяти PostgreSQL. Лаборатория использовала 100 соединений, три зарезервированы для суперпользователей, `reserved_connections=0`, PostgreSQL 18.6. Под реальной нагрузкой проверьте по ролям пределы приложения, общую нагрузку БД и эффект на CPU, RAM и commit latency.

Доступ к primary прямой либо через session pooling с сохранением server backend до освобождения session-level advisory lock. Transaction pooling требует отдельной проверки совместимости. Ingestion и Beat опираются на session fencing. Migration Job использует PostgreSQL lock на время миграции. Проверка failover должна подтвердить безопасное высвобождение сессий и возобновление outbox.

[PostgreSQL advisory locks](https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS) · [PostgreSQL statistics](https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-PG-STAT-ACTIVITY-VIEW) · [Параметры приложения](../../deploy/helm/aspm/values.yaml)

## Пики в OrbStack

| Фаза | Всего | Активные | Wait Lock | Idle in transaction | Сэмплы |
|---|---:|---:|---:|---:|---:|
| Mixed Classic/PATCH, DevSecOps и report | 12 | 1 | 0 | 0 | 4 |
| Concurrent scans, A 1/1 | 5 | 3 | 0 | 2 | 164 |
| Concurrent scans, B 2/3 с тем же общим бюджетом | 9 | 5 | 2 | 3 | 168 |
| Concurrent scans, C 2/3 с 2 CPU на Django | 13 | 5 | 1 | 1 | 164 |
| Rolling update, семь окон | 9 | 4 | 1 | 1 | 2431 |
| Worker replacement | 13 | 3 | 3 | 0 | 152 |
| Scale-up 1/1 → 2/3 | 9 | 1 | 0 | 1 | 520 |
| Возврат 2 → 3 worker | 10 | 0 | 0 | 0 | 156 |
| Report generation, три окна | 9 | 1 | 0 | 0 | 14 |
| Migration Job, два окна | 7 | 3 | 0 | 1 | 136 |
| Все фазы вместе | **13** | **5** | **3** | **3** | **8667** |

Максимумы столбцов рассчитаны независимо. Три ожидающих блокировку сессии наблюдались во время контролируемых worker-отказов с тестовой advisory lock. `active` и `waiting Lock` могут пересекаться. Смешанный короткий сценарий занял около секунды и дал четыре точки. Для окон отчёта использовался интервал от POST до первого наблюдаемого статуса COMPLETED. В окне Migration Job фоновые веб-запросы продолжались, поэтому строка показывает общий наблюдаемый пик во время Job. Использованы события SuccessfulCreate и Completed, а не оценка по длительности всего upgrade. [Сводные числа по фазам](raw/qualification-summary.json)
