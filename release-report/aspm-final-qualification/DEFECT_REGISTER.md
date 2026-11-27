# Реестр дефектов

| ID | Priority | Наблюдение и воспроизведение | Root cause | Исправление | Ретест |
|---|---|---|---|---|---|
| QA-001 | P1 | publish-images.sh завершался KeyError monitoring до обращения к registry | Устаревшее поле rc.10 выбирало SHA в манифесте rc.11 | 6eebcae0fa. Общий выбор application SHA по умолчанию и явный --monitoring | 3 регрессионных теста, реальный loopback push/pull двух ARM64-образов |
| QA-002 | P1 | POST скана с private root внутри media возвращал HTTP 500 | Исключение отказа в небезопасном пути проходило через слой DRF | c95177336f4d. HTTP 503 с сохранением запрета и без записи ScanRun/outbox | test_misconfigured_private_storage_rejects_acceptance_with_service_unavailable |
| QA-003 | P2 | System Health возвращал HTTP 400 при invalid private root и HTTP 500 при неподдерживаемом URL брокера | Исключения probe прерывали построение страницы | c95177336f4d. Состояние зависимости недоступно, остальная диагностика доступна | test_system_health_reports_misconfigured_private_storage |
| QA-004 | P2 | axe-core отметил цели на Findings | Размеры интерактивных целей на просмотренной странице | Открыт | [Отчёт axe](ACCESSIBILITY_REPORT.md) |
| QA-005 | P2 | START_HERE ссылался на rc.10 в блоке rc.11 и на архивный путь при работе из Git | Документы указывали разные источники сборки | 6eebcae0fa. Уточнены SHA, layout Git и явный --chart | Сборка из git archive и упаковка чарта |

QA-006 (P2, тестовое окружение). Первый SLA-замер включал два SELECT и DELETE для устранения дубликата глобальной строки Notifications. Второй замер использовал нормализованную fixture. Исправление 4bad355ced переносит разрешение дубликата до CaptureQueriesContext. Assertions сохранены. Повтор seed 128 прошёл 33 из 33. Наблюдавшийся OOM на узле и обрыв первого тестового окружения приведены в [Kubernetes отчёте](KUBERNETES_HA_REPORT.md) и [регрессии](FINAL_REGRESSION.md). Кандидат остаётся HOLD до прохождения gates.

| Priority | Воспроизведено | Исправлено | Осталось |
|---|---:|---:|---:|
| P0 | 0 | 0 | 0 |
| P1 | 2 | 2 | 0 |
| P2 | 4 | 3 | 1 |
| P3 | 0 | 0 | 0 |

Таблица относится к зарегистрированным дефектам ASPM и его тестов. Пакетные CVE и инфраструктурные ограничения приведены отдельно в SECURITY_REPORT и RELEASE_GATE.
