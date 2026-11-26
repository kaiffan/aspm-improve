# Матрица квалификации

| Блок | Кандидат / окружение | Проверка |
|---|---|---|
| Django | bef347c845ee, отдельный Compose | 8 357 PASS, 553 inherited skips, 0 failures/errors. Строгий API-only 86/86 в пятой БД |
| JavaScript | bef347c845ee | 17/17 для тем, фильтров и evidence polling |
| Helm | 0.1.0-rc.9 | 20/20, lint/schema/manifest по профилям, server dry run и live Helm test |
| Classic | Local OrbStack | Product Type, Product, Engagement, Test, Legacy import/reimport, Finding PATCH и Classic Report |
| DevSecOps | Local OrbStack | Шесть форматов, три параллельных клиента, одна commit identity, replay, хеши оригиналов и HTML/JSON |
| Browser | Local Chromium | 240 состояний, 11 проверок, 0 ошибок. Восемь viewport, Light/Dark/System, клавиатура и Native HTML Report |
| OpenAPI и миграции | Local OrbStack | v2 209, v3 41, ASPM 11 paths. Структуры совпадают с базой после исключения servers. No changes detected |
| Доступ | Local OrbStack / Django | Серверные cross-scope отказы по оригиналам/выгрузкам и scoped credentials |
| Keycloak UI | Предыдущий eee10e678c77, TLS | 6 test профилей, Android-подобные и desktop widths. Revocation при TTL 120 с |
| Webhooks | Strict suite | HMAC/TLS test receiver, retries, replay, RBAC и правила доставки |
| Concurrent writes | Django | PATCH/PATCH, PATCH/reimport/asynchronous task, dedup, 5 политик, competing ScanRun, outbox и immutable snapshots |
| PostgreSQL recovery | Синтетическая DB | Dump checksum, restore в пустую DB, сверка 388 миграций, 3 Products, 6 ScanRuns и 1 Report. Guard непустой цели. Восстановленные оригиналы и оба формата отчёта прошли SHA-256 |
| Performance / pod HA | HA Stabilization eee10e678c77 | Исторические измерения отдельного кандидата |

Ранее eee10e678c77: 8356/8909 Django passed, 553 inherited skips, 0 failures. JavaScript 17, Helm 19. 208 состояний Chromium, 36 действий и 6 Keycloak profiles. [Отдельный отчёт производительности](PERFORMANCE_REPORT.md) · [Отказоустойчивость](FAILOVER_REPORT.md) · [Установка](CLEAN_INSTALL_REHEARSAL.md)

Полный перечень ID и статус каждого Django теста в evidence/django-results.tsv.gz. Сравнение наборов подтвердило сохранение всех 8 909 исходных тестов и одну новую проверку Finding table. [Сводка Django](evidence/django-summary.json) · [Chromium](evidence/browser-results.json) · [Live run](evidence/live-functional.txt)
