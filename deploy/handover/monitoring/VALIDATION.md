# Квалификация мониторинга на изолированном стенде

27 ноября 2026, OrbStack ARM64, Kubernetes v1.36.5, ASPM 1.0.1, chart 0.1.0-rc.10. Прогон использовал локальный Django image на основе handover bef347c845ee и новую инструментацию. Снаружи корпоративного контура работали Prometheus 3.5.1, VictoriaMetrics 1.122.0, Grafana 12.3.9, postgres_exporter 0.19.1, redis_exporter 1.81.0 и kube-state-metrics 2.17.0.

| Gate | Статус и подтверждение |
|---|---|
| APPLICATION METRICS | PASS для HTTP, синтетических ScanRun, снимков наблюдений и generated reports. Успешная загрузка HTTP 202, дубликат HTTP 200, отдельный failed scan, generated HTML/JSON. |
| MULTIPROCESS METRICS | PASS. Два независимых процесса записали 2 + 3 событий, histogram count и webhook counter вернули 5. При запуске следующего процесса с очисткой каждое значение стало 1. |
| PROMETHEUS SCRAPE | PASS на всех 10 targets профиля 2 web, 3 worker, beat, Prometheus, PostgreSQL exporter, Valkey exporter и kube-state-metrics. Тест Helm охватывает ingress selector. |
| LOCAL REMOTE_WRITE | PASS, TLS с локальным CA, scoped filter и сохранение WAL на PVC. При отключении 81 с retried_samples вырос на 3 136, VictoriaMetrics позже вернула 5 исторических samples с каждого web target. |
| VICTORIAMETRICS QUERY | PASS. Прямой HTTPS query API вернул 19 ScanRun accepted, 18 completed, 1 failed, 18 новых Findings и 1 сгенерированный отчёт в проверенном окне. |
| GRAFANA DASHBOARDS | PASS для 9 импортированных JSON, 105 панелей и 126 запросов через datasource proxy. 74 панели получили числовые данные за 15 минут. Остальные серии условны либо не наблюдались в окне. |
| ALERT RULES | PASS, promtool подтвердил 32 alerts, 7 recording rules и отдельный dead-man example. В локальном evaluator ASPMRemoteWriteStalled прошёл firing → resolved. Окно проверки сокращено до 30 с и порог до 15 с только на стенде. |
| MONITORING OVERHEAD | REVIEW. Короткий A/B на общем хосте, отражает только измеренные запросы и сканы. В длительном прогоне узел перезапускал pods при нехватке памяти, итоговый стенд переведён на меньший профиль. |
| MONITORING HANDOVER | READY для передачи исходников, chart, dashboards, инструкций и результатов стенда. |
| CORPORATE REMOTE_WRITE | PENDING. Нужны авторизованные параметры владельца и проверка корпоративного адреса. |
| CORPORATE GRAFANA | JSON READY. Импорт выполняет владелец с существующим VictoriaMetrics datasource. |

### A/B

Одинаковые 16 Semgrep ScanRuns при concurrency 4, 100 отдельными HTTP запросами и одинаковыми лимитами приложения. Измерение через локальный port-forward. Внутренние серверные метрики и клиентские timings сравниваются отдельно.

| Показатель | Monitoring off | Monitoring on |
|---|---:|---:|
| HTTP probe, запросов/с | 341,56 | 250,15 |
| HTTP probe p95, мс | 29,4 | 44,2 |
| Scan HTTP acceptance p95, мс | 443,5 | 383,6 |
| Scan completion p95, мс | 979,8 | 928,1 |
| Завершённых ScanRuns/с | 5,892 | 6,094 |

В момент контрольного запроса Prometheus оценила 14 622 head series, включая exporter и инфраструктуру. Этот snapshot включает ряды pod после rollout и экспортёры PostgreSQL. CPU/RAM, I/O, SQL и сетевой трафик не были измерены парным продолжительным тестом. Повторите прогон на выделенном staging, прежде чем утверждать бюджет overhead. Поведение OOM на общем локальном узле ограничивает выводы о длительной нагрузке.

### Доступные результаты

- [Baseline](evidence/workload-baseline.json), [monitoring enabled](evidence/workload-enabled.json)
- [Ответы VictoriaMetrics](evidence/victoriametrics-query.json), [remote write recovery](evidence/remote-write-recovery.json)
- [Проверка каждой панели](evidence/dashboard-queries.json)
- [Скриншот Operations Control Center](screenshots/01-control-center.png), [скриншот Monitoring Pipeline](screenshots/07-monitoring-pipeline.png)

### Границы стенда

Компактное испытание включает замену web/worker pod при rollout и повторный scrape. Отдельный сценарий broker outage с рабочей очередью, HTTP retry вебхука, живой Keycloak, корпоративный Alertmanager routing, mTLS/basic/bearer на стороне корпоративной VictoriaMetrics и проверка vmalert остаются открыты. cAdvisor, Traefik, внешние node и CSI metrics требуют соответствующих источников. В Security Posture проверены проекты, репозитории, active Findings и активность сканеров. Coverage и stale scan требуют утверждённой политики ожидаемых сканеров, а тренды false positive/mitigation требуют отдельной истории переходов. Production qualification и Linux/AMD64 image qualification остаются открыты.

### Проверка переноса и своего registry

С исходным архивом и runtime patch выполнены сборка двух release-образов ARM64, push во временный registry, pull и сравнение по digest. В новом namespace Kubernetes скачал образы из registry с Always. Команда deploy.sh выбрала Helm 0.1.0-rc.10 из манифеста, прошла preflight и миграции, подтвердила три health HTTP 200, Helm test и рабочий /login. Web, worker, Beat и Prometheus стали UP в Targets. Registry в доказательствах локальный и относится к испытанию. [Результаты переноса](evidence/portable-build.json) · [Команды для другого компьютера](../docs/18_BUILD_AND_IMAGE_TRANSFER.md)

Оба образа отдельно собраны без кэша BuildKit. В Django проверен импорт exporter, в nginx проверены исполняемый файл и статические файлы ASPM. Свежая пара также прошла push и pull с проверкой registry digest.
