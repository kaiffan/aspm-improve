# Два рабочих пространства ASPM

Classic и DevSecOps работают в одном приложении, используют одну базу PostgreSQL, единый Keycloak SSO и действующие механизмы авторизации, аудита и отчётности DefectDojo.

| Пространство | Путь по данным | История |
| --- | --- | --- |
| Classic | Product Type → Product → Engagement → Test → Finding → Reports | Текущее состояние Findings, штатные import/reimport и отчёты DefectDojo |
| DevSecOps | Product как Project → Repository → Commit → ScanRun → оригинал, исторические Findings и версии отчётов ASPM | Неизменяемые FindingObservation и снимки выбранных завершённых сканирований |

В Classic внешний API принимает сканирование по существующему Engagement или Test. Repository, Commit и SHA нужны только Git-сценарию. DevSecOps назначает Engagement по действующей политике и связывает ScanRun с реальным Test. На одном Product могут одновременно существовать оба вида Tests. Классические метрики читают существующие Findings. Данные снимков используются в отчётах конкретных коммитов и не добавляют строки Findings в классические агрегаты.

В Scanner Reports на странице коммита видны ссылки на связанные Test и Engagement. С Classic Test можно вернуться к точному ScanRun на вкладке оригиналов. Classic Product выводит ссылку на свои репозитории, когда они существуют. Обычный Test без ScanRun отображает свою классическую иерархию.

## Развёртывание

Один Helm release обслуживает оба пространства через один web, worker, beat и migration job. Он использует общие PostgreSQL, Keycloak, Celery, Redis/Valkey и приватное хранилище. Существующие webhooks, правила мониторинга и API остаются частью той же установки. Ссылки между пространствами используют маршруты Django, поэтому оба доступны через существующий ingress.

Локальная проверка Kubernetes выполнялась в режиме server-side dry-run. На единственном узле лаборатории наблюдались `DiskPressure=True` и `node.kubernetes.io/disk-pressure:NoSchedule`. Для живой проверки релиза требуются пригодные для планирования узлы и staging. [Результаты регрессии](CLASSIC_AND_DEVSECOPS_REGRESSION.md)
