# Аудит кандидата ASPM 1.0.1

Handover фиксирует application bef347c845ee, chart 0.1.0-rc.9 и manifest eda4deeeca.

| Источник на кандидате | Семантика и ограничения | Реализация |
|---|---|---|
| django-prometheus 2.5.0 | HTTP middleware, DB instrumentation, /django_metrics/metrics. Без multiprocess directory endpoint видел данные ответившего uWSGI процесса. | Legacy сохраняется с прежними values. В opt-in режиме ASPM HTTP middleware заменяет legacy HTTP middleware, а DB instrumentation сохраняется. |
| Chart ServiceMonitor | Web scrape на 8081. Worker и singleton отсутствуют. Ссылка на scrape Secret не задана. | Новый ServiceMonitor или PodMonitor собирает отдельные exporter targets 9108, доступ контролирует NetworkPolicy. |
| nginx | Маршрутизация и probes. Stub status и exporter есть в upstream chart. | Django наблюдает application responses. Upstream 504 и TLS наблюдаются средствами Traefik. |
| Webhooks | ATTEMPTS, DURATION, EXPANDED локальны процессу. Gauges pending/oldest были локальными, custom collector выполнял SQL при каждом scrape. | Существующие counters и histogram агрегируются из файлов pod. Бизнес-gauges обновляет singleton вне scrape. |
| Celery | Worker readiness ping и task logs. | Сигналы Celery дают heartbeat, runtime и результаты, parent process даёт active и reserved. |
| ScanRun | Сохранялись parser/reimport/snapshot timestamps и status. | Метрики используют эти timings и durable transitions. |
| PostgreSQL / Valkey | Внешние instances, Helm не создавал exporter. | Корпоративные либо опциональные exporters. Для БД используется роль с pg_monitor. |
| KSM / cAdvisor / CSI / Traefik | Инфраструктурные источники за пределами приложения. | Подключаются с согласованными scope labels. |
| Grafana / алерты | Текстовые инструкции без dashboard JSON и rules. | Дашборды, recording rules, alert rules. |

[Каталог метрик реализации](METRIC_CATALOG.md)
