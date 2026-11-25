# Регрессия Classic и DevSecOps

До реализации на `0352960ff143b9fd8037f5f72525afe32b29e6fd` прошли 217 тестов. В браузере было видно, что политика Keycloak закрывала EXPERT и USER вход в часть Classic разделов. После реализации проверены штатные API, браузер под локальными Keycloak principals и восстановление в отдельную базу.

На финальном исходном коммите `c5ed33b99c9a33afa1dcc3c220956d9424679180` прошло 8 353 из 8 906 Django тестов, 553 штатно пропущены, ошибок и падений нет. Дополнительный строгий прогон API-only прошёл 47 тестов. Прошли 17 JavaScript тестов, 13 Helm тестов и проверка схемы миграций. [Результаты запуска](dual-raw/test-results.json)

| № | Сценарий | Свидетельство |
| --- | --- | --- |
| 1 | Product Type create | Chromium, SECOPS, v2 HTTP 201 |
| 2 | Product create | Chromium, SECOPS, v2 HTTP 201 |
| 3 | Engagement create | Chromium, EXPERT, v2 HTTP 201 |
| 4 | Test create | `test_secops_classic_creation_uses_existing_endpoints`, штатный v2 Tests API |
| 5 | Legacy import без Git | Chromium, v3 HTTP 200, v2 штатный токен в `test_legacy_machine_import_reimport_without_git_metadata` |
| 6 | Legacy reimport | Chromium, v2 HTTP 201 и существующая регрессия import/reimport |
| 7 | Ручное создание Finding | Chromium, v2 HTTP 201 |
| 8 | Finding PATCH | Chromium, v2 HTTP 200 и модульные RBAC проверки |
| 9 | Concurrent PATCH/reimport | `test_finding_write_concurrency`, включая применение PATCH при устаревшем reimport и реальные import/dedup проверки |
| 10 | False Positive | Chromium подтвердил поле `false_p`, Django подтвердил сохранение исторического снимка |
| 11 | Test HTML Report | Chromium, HTTP 200 и Finding в HTML |
| 12 | Engagement Report | Chromium, HTTP 200 и Finding в HTML |
| 13 | Product Metrics | `test_product_metrics_aggregation`, `test_product_metrics_closed_count` |
| 14 | Product Stats | `test_product_stats` |
| 15 | DevSecOps upload с Commit | `test_aspm_ingestion` |
| 16 | Автоматическое назначение Engagement | `test_aspm_engagement_policy` |
| 17 | Zero-Finalize | `test_aspm_zero_finalize`, отчёт после завершённых ScanRuns |
| 18 | Generated ASPM Report | `test_aspm_ingestion`, версии, замороженный manifest и байты |
| 19 | Commit Diff | `test_aspm_zero_finalize`, полное и неполное покрытие |
| 20 | Classic и Git Tests в одном Product | Chromium и fingerprint восстановленного Product |
| 21 | Cross-Product isolation | Chromium HTTP 404 для чужого Test, Django для UI, API и отчётов |
| 22 | Classic API после Keycloak | Chromium, разрешённые операции EXPERT/SECOPS и ограниченный USER |
| 23 | Старый scoped machine integration | Live v2/v3 со штатным DRF-токеном и запретом для чужого Product, модульные проверки ASPM scope |
| 24 | Навигация между пространствами | Chromium, Classic и DevSecOps через точный Test/ScanRun |
| 25 | Backup/restore обоих путей | Сравнение JSON по 11 моделям, 46 файлов по SHA-256 и один Product с обоими путями |

Предыдущий тест запрещал Classic API даже при выданном объектном разрешении. В актуальной регрессии тот же защищённый режим возвращает HTTP 403 без разрешения и HTTP 201 после выдачи разрешения. Отдельный прежний тест подтверждает блокировку браузерной загрузки в том же режиме. Проверки лимитов multipart используют аутентифицированный запрос, чтобы дойти до валидации payload.

## Воспроизведение

Полный набор запускается штатной обёрткой `./run-unittest.sh --test-case unittests` в тестовом Docker Compose с отдельной базой и выделенными кэшем и брокером. Сценарий Chromium принимает каталог синтетических аккаунтов и каталог для снимков экрана. Скрипт восстановления выполняется через Django shell в исходной лаборатории и в отдельном restore-окружении. [Подготовка лаборатории](../../deploy/labs/keycloak/README.md) · [Сценарий Chromium](../../deploy/labs/keycloak/dual_workspace.cjs) · [Манифест восстановления](../../deploy/labs/keycloak/restore_manifest.py)

## Лабораторные артефакты

- [Исходная проверка Keycloak](dual-raw/baseline-browser.json), [итоговые браузерные проверки](dual-raw/browser.json) и [скриншоты](CLASSIC_WORKSPACE_UI.md).
- [Штатный сервисный токен](dual-raw/native-machine.json) и [проверка классических форм](dual-raw/classic-forms.json).
- [Хеши OpenAPI](dual-raw/openapi-sha256.txt) и [fingerprint восстановления](dual-raw/restore-manifest.json).
- [Helm и Kubernetes](dual-raw/deployment-checks.txt). Helm lint, шаблоны и валидация Kubernetes выполнены. Server-side dry-run принят локальным API Kubernetes. Запуск Pods на staging и production остаётся непроверенным.

Бэкап снят с синтетической базы лаборатории. Восстановление выполнено в свежее имя базы и новый Docker volume, совпадение подтверждено по хешам. Старые данные Mac сохранены. База, подлежащая очистке, не была однозначно идентифицирована.
