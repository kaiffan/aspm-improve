# ASPM API-only: реализация и проверка

Дата: 24 ноября 2026. Ветка: `codex/aspm-api-only-ingestion`, содержит `origin/dev` и предназначена для следующего релиза из `dev`.

Implementation Git SHA: `3fbb68543265f5393cf538943011c5c0ecdbde0e`. Последующий commit добавляет этот отчёт, актуальную сгенерированную схему и доказательства проверки. Проверяемый RC5 baseline: `3000b9755021667db4c1c8960771913c240761a4` (`codex/rc5-candidate-v5`). Файлы `dojo/finding/` и `dojo/aspm/release.json` относительно него не изменены. Исходный checkout и RC5 worktree сохранены. Stable не публиковался. [Проверка baseline](../../perf-report/aspm-api/baseline-integrity.json).

## Реализованный контракт

Рабочая цепочка: существующий Product → Repository → Commit → независимые ScanRuns → приватные оригиналы → исторические observations. Отдельно Commit → зафиксированный ScanSet → версии GeneratedReport с собственными HTML/JSON. UI принимает только запросы просмотра и скачивания; browser import/reimport routes закрыты на GET и POST. Общий запрет upload действует и для старых страниц DefectDojo.

Полный контракт, правила выбора Test, deployment и lifecycle описаны в [README](README.md). Машиночитаемая [OpenAPI 3.0.3 specification](openapi.yaml) получена из DRF views и проверена через `spectacular --validate --fail-on-warn`. Django namespace — `aspm_v1`; пути учитывают существующий installation URL prefix.

| Метод | Реальный путь |
|---|---|
| POST | `/api/aspm/v1/scans/` |
| GET | `/api/aspm/v1/scans/{uuid}/` |
| POST | `/api/aspm/v1/scans/{uuid}/retry/` |
| GET | `/api/aspm/v1/scans/{uuid}/artifact/` |
| GET | `/api/aspm/v1/projects/{id}/repositories/` |
| GET | `/api/aspm/v1/repositories/{id}/commits/` |
| GET | `/api/aspm/v1/commits/{id}/scans/` |
| POST | `/api/aspm/v1/commits/{id}/finalize/` |
| POST, GET | `/api/aspm/v1/commits/{id}/reports/` |
| GET | `/api/aspm/v1/reports/{uuid}/download/?format=html` или `format=json` |
| GET | `/api/aspm/v1/openapi/` |

Пример доставки, где Product уже существует, а токен ограничен этим Product:

```sh
curl --fail-with-body --silent --show-error \
  -H "Authorization: ASPM $ASPM_TOKEN" \
  -H "Idempotency-Key: gitlab/project-17/pipeline-52/job-93/attempt-1/semgrep" \
  -F project_id=17 \
  -F repository_url=https://gitlab.example.org/team/service \
  -F commit_sha=0123456789abcdef0123456789abcdef01234567 \
  -F 'scanner_type=Semgrep JSON Report' \
  -F file=@semgrep.json \
  "$ASPM_URL/api/aspm/v1/scans/"

curl --fail-with-body -H "Authorization: ASPM $ASPM_TOKEN" \
  "$ASPM_URL/api/aspm/v1/scans/$SCAN_ID/"
```

После доставки обоих scanner jobs оркестратор с отдельными `read,finalize,reports,status` scopes фиксирует именно IDs текущего pipeline:

```sh
curl --fail-with-body -X POST \
  -H "Authorization: ASPM $ASPM_REPORT_TOKEN" -H 'Content-Type: application/json' \
  -d '{"expected_scanners":["Semgrep JSON Report","Trivy Scan"],"scan_ids":["<semgrep-uuid>","<trivy-uuid>"]}' \
  "$ASPM_URL/api/aspm/v1/commits/$COMMIT_ID/finalize/"

curl --fail-with-body -X POST \
  -H "Authorization: ASPM $ASPM_REPORT_TOKEN" -H 'Content-Type: application/json' \
  -d "{\"scan_set_id\":\"$SCAN_SET_ID\"}" \
  "$ASPM_URL/api/aspm/v1/commits/$COMMIT_ID/reports/"
```

Исполняемые примеры: [curl upload](../../examples/aspm-ci/upload.sh), [GitLab CI](../../examples/aspm-ci/gitlab-ci.yml), [GitHub Actions](../../examples/aspm-ci/github-actions.yml), [ожидание/finalize/download](../../examples/aspm-ci/finalize.py). Образы сканеров задаются установкой; CI secrets должны быть protected/masked. Hosted GitLab/GitHub workflows здесь не запускались. Сам helper выполнен через настоящий локальный HTTP API: [результат](../../perf-report/aspm-api/ci-finalizer.json), [сформированный HTML](../../perf-report/aspm-api/generated-example/report-v3.html), [JSON](../../perf-report/aspm-api/generated-example/report-v3.json). Версия 3 содержит ровно два выбранных ScanRuns и шесть observations; checksums сверены, CVE сохранены.

## Authentication и RBAC

`Authorization: ASPM <secret>` использует отдельный активный service account без staff/superuser и с unusable password. База хранит только digest. Токен содержит Product, optional Repository, scopes, expiry и revoke. Авторизация проверяется до multipart parsing; обычные sessions и DD tokens не дают права новых ASPM мутаций. Чтение человеком использует существующий Product RBAC. Status/artifact CI ограничены собственным service user и границами токена.

Через [HTTP security checks](../../perf-report/aspm-api/security-http.json) также проверены очистка небезопасного имени файла, byte-exact download и защитные headers. Проверены истечение, отзыв, scopes, чужой Product, подмена Repository/Commit/ScanSet, чужой service user, SSO human account, обычная пользовательская сессия, точный общий DB rate counter и скачивание по RBAC. Старый ASPM secret не становится глобальным DefectDojo token. Legacy v2/v3 сохраняют API authentication и Product RBAC; обычный human account не может использовать их для обхода запрета. Старые административные интеграции и явно enrolled machine accounts могут выполнять import/reimport без Git metadata.

Стандартный предел оригинала — 50 MiB, rate — 120 запросов/минуту на токен, включая polling. Есть потоковый предел размера, проверка scanner factory, полного SHA, timestamps, URL и неизвестных полей. Пути хранения генерирует сервер; имя файла — очищенная display metadata. Parser/SQL logs ASPM import не содержат входного содержимого; [проверка отсутствия CI/session secrets в логах](../../perf-report/aspm-api/log-privacy.json) выполнена для логов этого стенда. Она не доказывает отсутствие любых возможных секретов в произвольных third-party parsers или внешнем gateway.

## Idempotency, import/reimport и data integrity

Один `(Product, delivery_key)` обозначает одну логическую доставку. Fingerprint включает файл и нормализованные metadata. Первый приём — 202, точный повтор — 200 с тем же ScanRun, несовпадение — 409. Новый job attempt или scanner получает новый ключ и Test, даже при одинаковых байтах. Конкурирующие запросы сериализуются короткими DB transactions/unique constraints после сохранения оригинала.

Каждый ScanRun получает собственные Engagement/Test внутри Commit. Пустой Test создаётся штатным DefaultImporter, загрузка и retry используют штатный DefaultReImporter, matching и synchronous dedup внутри Celery. Retry использует тот же зарезервированный Test. Следующий commit никогда не reimport-ится в Test предыдущего ScanRun. Отдельный ASPM parser отсутствует; Semgrep/Trivy обрабатывались существующими parsers.

Оригиналы побайтно сохраняются в `/app/aspm-private` под UUID, отдельно от MEDIA/STATIC/nginx, с mode 0600/0700, SHA256, размером и fsync перед DB commit. Worker повторно проверяет целостность. Скачивание — через авторизованный FileResponse с attachment/no-store/nosniff/CSP. Это application-level immutable storage; объектный WORM и защита от привилегированного администратора ОС в этой реализации не заявляются.

Lifecycle: `ACCEPTED → PROCESSING → COMPLETED | FAILED`; явный retry FAILED снова ставит ACCEPTED. Транзакционный outbox сохраняется до фактического terminal state. On-commit wake ускоряет отправку, beat/management command восстанавливают недоставленные задания. Advisory lock на ScanRun предотвращает двойную обработку, штатный shared Test lock охватывает importer и snapshot. Длительные parsing/file I/O не выполняются под PostgreSQL row locks. RC5 Finding concurrency protocol остаётся прежним.

Новая generation observations публикуется атомарно только после dedup и полного snapshot. Observations хранят значения, включая CWE и актуальные vulnerability references; не являются FK к изменяемому Finding. DB guards защищают Product/Repository/Commit/Test связи, оригиналы, завершённые snapshots, ScanSets и версии отчётов. Новые миграции `0310`–`0315` добавлены поверх существующих цепочек; граф имеет единственный leaf `0315_aspm_source_relationship_guards`.

Finalize фиксирует IDs и ожидаемые scanner types, а не объявляет покрытие полным. Отчёт фиксирует статусы/generations этого набора при регистрации. Отсутствующий scanner, FAILED или ещё не завершённый выбранный запуск дают `complete=false`. Поздняя доставка требует нового finalize; старые версии и bytes не меняются. Для нового pipeline helper передаёт конкретные IDs: старый успешный scanner не маскирует пропущенный текущий job. Severity summary считает observations независимых запусков, включая flags duplicate; это не число уникальных активных уязвимостей проекта.

## UI только для просмотра

Навигация: Product → Repositories → Repository → Commit → Commit evidence. Вкладки: Overview, Original Scanner Reports, ASPM Generated Reports, Historical Findings, Commit Changes. Есть severity filter, cursor по 50 observations, сравнение коммитов и авторизованные downloads. Форм и кнопок загрузки сканов нет; три legacy browser import/reimport маршрута возвращают 404 и на POST.

Playwright/Chromium проверил одиннадцать поверхностей (включая обе legacy-формы создания Engagement) × две ширины (1440/390) × две темы = 44 страницы: нет file inputs, multipart forms, upload links, JS errors и горизонтального переполнения viewport; JSON download содержит платформенный отчёт. [Результат](../../perf-report/aspm-api/browser.json), [сценарий](../../perf-report/aspm-api/browser.cjs), [desktop screenshot](../../perf-report/aspm-api/screenshots/reports-1440-dark.png), [mobile screenshot](../../perf-report/aspm-api/screenshots/findings-390-light.png). Playwright MCP в сессии отсутствовал, использован установленный Playwright CLI. Интерактивное открытие HTML на миллион строк в браузере не проверялось.

## Обязательные интеграционные сценарии

| № | Сценарий | Подтверждение |
|---|---|---|
| 1–4 | Semgrep и Trivy для одного Commit, два независимых ScanRuns, оригиналы побайтно | Unit + настоящий HTTP/Celery, Semgrep 1 и Trivy 5 findings |
| 5 | Повтор POST без дубля | Unit; HTTP возвращает тот же UUID и 200 |
| 6 | Конкурентный одинаковый ключ | PostgreSQL TransactionTestCase с 4 запросами; HTTP с 8 запросами: один 202, семь 200 |
| 7 | Новая попытка job сохраняет историю | Unit: новый ключ, отдельные ScanRun/Test |
| 8 | Следующий commit/reimport не меняет observations | Unit, включая изменение текущего Finding |
| 9 | Точный состав GeneratedReport | Unit + HTTP + helper: ровно выбранные IDs |
| 10 | Поздний scan не меняет старый отчёт | Unit + сравнение HTML/JSON bytes/checksums через HTTP |
| 11 | Чужой Product запрещён CI token | Unit и HTTP; дополнительные scope/expiry/revoke/ownership проверки |
| 12 | Legacy import/reimport без Git metadata | Настоящие parsers в unit integration; прежние API suites |
| 13 | Ошибка parser/worker, явный FAILED, безопасный retry | Unit + три реальных SIGKILL только своего worker child; retry завершил 4000 findings в том же Test |
| 14 | Нет UI загрузки | Unit GET/POST routes + 44 browser страницы |
| 15 | Конкурентная нагрузка без повреждений/утечек | 24 репозитория, concurrency 8, все 27 ScanRuns завершены; точные связи, RBAC, DB guards; это ограниченная локальная нагрузка |

Исходники: [integration tests](../../unittests/test_aspm_ingestion.py), [HTTP validator](../../scripts/validate_aspm_api.py), [worker fault scenario](../../perf-report/aspm-api/worker_faults.py). Доказательства: [HTTP](../../perf-report/aspm-api/http.json), [worker recovery](../../perf-report/aspm-api/worker-recovery.json). После трёх смертей worker зафиксирован FAILED `worker_recovery_limit`; explicit retry завершился на attempt 4, Test 114 не изменился. Broker failure/outbox gap и повторные Celery messages дополнительно проверены unit-тестами.

## Полная Django regression

Полный корпус на окончательном implementation SHA `3fbb68543265f5393cf538943011c5c0ecdbde0e`: **8815 тестов, 8262 passed, 553 skipped, 0 failures/errors**, 393.796 с. Дополнительно **37/37 targeted**, включая **20/20 strict API-only**. Счётчики и SHA256 полного лога: [tests.json](../../perf-report/aspm-api/tests.json), [полный сжатый лог](../../perf-report/aspm-api/django-full.log.gz).

Повтор на сохранённом `--keepdb`/cache состоянии сначала дал восемь расхождений в exact query-count tests importer/SLA. После пересоздания только изолированной тестовой БД и очистки только её кэша полный корпус прошёл; ожидаемые query counts не менялись. Полный benchmark и рабочая БД стенда сохранены. UI regression дополнительно проверен на предыдущем шаблоне: тест падает с пропущенной import-кнопкой и проходит после исправления.

Корпус legacy UI запускается в test-only compatibility mode; ASPM test classes явно включают `ASPM_API_ONLY=True`. Production default остаётся API-only. Тестовый wrapper и unittest images отключают API-only только для проверки прежних upstream сценариев импорта через UI. Строгий запуск: `ASPM_TEST_API_ONLY=True ./run-unittest.sh --test-case unittests.test_aspm_ingestion`. Test-only mode не используется в рабочем HTTP стенде.

`manage.py check` — без errors, с одним environment warning `staticfiles.W004`: в test image нет `/app/components/node_modules`; браузер получает статику через gateway. `makemigrations --check --dry-run` — No changes detected. Отдельная ASPM schema и существующая глобальная API schema проходят `spectacular --fail-on-warn`; migration graph check проходит.

## JavaScript regression и lint

Все **12 JavaScript tests** `release/1.0.1/scripts/theme.test.cjs` прошли; browser matrix выше также без JS errors. Shell syntax и `git diff --check` проходят. Изменённые Python файлы, кроме generated migrations (они исключены repo config), проверены локальным Ruff 0.15.13 с временной копией repo config: удалены только неизвестные этой версии ignore selectors `PLW0717`, `RUF105`, `RUF201`; исходный `ruff.toml` не менялся. Полный CI с версией Ruff проекта остаётся release gate.

## Performance: API upload и конкурентные доставки

Изолированный Docker Compose на Apple M5/16 GiB. App: 2 CPU/1536 MiB, PostgreSQL 18.6: 1 CPU/768 MiB, Valkey: 0,25 CPU/128 MiB, Celery prefork concurrency 2. Полный [environment](../../perf-report/aspm-api/environment.json) включает версии ПО и образы. Стенд использует source overlay поверх существующего test image; новая release image не собиралась и не публиковалась.

Настоящие HTTP/Celery/PG, небольшие scanner fixtures, concurrency 8:

| Метрика | Медиана | p95 / максимум |
|---|---:|---:|
| HTTP upload end-to-end, 26 samples | 120,69 ms | p95 171,63 ms; max 197,39 ms |
| Сохранение оригинала, 27 runs | 12,07 ms | max 19,44 ms |
| Celery publish → worker start | 496,38 ms | max 936,80 ms |
| Parser execution | 5,85 ms | max 7,61 ms |
| Штатный reimport/dedup после parsing | 17,67 ms | max 144,94 ms |
| Observation snapshot | 3,17 ms | max 5,94 ms |
| Generated HTML+JSON, малый отчёт | 13,62 ms | один замер |

24 независимые загрузки разных repositories приняты за 418,70 ms. Все 27 запусков функционального сценария завершились. p95 — nearest rank; [raw samples](../../perf-report/aspm-api/http.json). Чистое queue wait отделено от acceptance-to-start/outbox; оно не объявляется измеренным для crash redelivery. В отдельном worker recovery сценарии 4000 findings: parser 0,215 с, reimport/dedup 17,770 с, snapshot 0,216 с. Эти данные не задают throughput SLA для тяжёлых parsers или больших файлов.

## Performance: историческая модель на 1 млн findings

В отдельной БД созданы ровно **1 000 000 живых Finding rows** и **1 000 000 FindingObservation rows**. Fixture склонирован SQL, по 10 000 строк; production snapshot и report generator выполнялись без подмены. Fixture не моделирует parser/reimport throughput миллиона findings. Объёмы 5–20 млн не создавались.

| Метрика | Измерение |
|---|---:|
| Первичное создание synthetic fixture | 289,62 с |
| Snapshot 1 млн observations | **93,32 с** |
| WAL delta во время snapshot | **1 950 969 808 bytes** |
| Генерация HTML+JSON | **15,47 с** |
| Finding table + indexes | 1 163 091 968 bytes |
| Новые observations: table / indexes | 682 893 312 / 328 654 848 bytes |
| Новые observations вместе | **1 011 548 160 bytes** |
| JSON generated report | 624 778 857 bytes |
| HTML generated report | 1 037 669 246 bytes |
| Экспорты вместе | **1 662 448 103 bytes** |
| Историческая UI page: 50 rows, 5 cursor pages | median 10,93 ms; max 122,52 ms |

WAL измеряется через разницу cluster LSN, не изолирован per database; во время замера возможен вклад коротких функциональных запросов в другую БД того же PostgreSQL. Fixture seed WAL также не относится к стоимости исторической модели. В benchmark нет миллиона CVE-reference rows: стоимость массовых vulnerability references отдельно не измерена. UI timing — Django TestClient, реальная PG и template rendering, без network/browser. Большие HTML/JSON генерировались потоково, размеры и checksums записаны; browser rendering 1 GB HTML не является результатом теста.

Доказательства: [1M benchmark](../../perf-report/aspm-api/history-1m.json), [fixture seed](../../perf-report/aspm-api/fixture-seed.json), [UI cursor](../../perf-report/aspm-api/history-ui.json). Для воспроизведения в специально выделенной БД `aspm_history_*`: `python manage.py benchmark_aspm_history --rows 1000000 --confirm-isolated-database`. Команда ограничена максимумом 1 млн; повторный запуск требует отдельной пустой fixture БД/подготовленного synthetic Test, как описано в её `--help`. Обычную рабочую БД она не принимает.

## Release readiness

Функциональная реализация и локальная квалификация завершены; ветка готова к code review и CI. **Production release readiness пока не подтверждена**, Stable не публиковался. Не выполнялись hosted GitLab/GitHub pipelines, production HA/multi-host failover, работа через PgBouncer, новый image build/release pipeline и capacity-тесты тяжёлых реальных scanner reports. Сохранившаяся footer/release metadata старого test image не является новым релизом ASPM.

Перед promotion нужны штатный CI на итоговом SHA, сборка app/worker images, deployment с общим приватным storage, проверка restore БД+evidence, TLS/ingress limits и sizing под реальные parser profiles. Для session advisory locks требуется direct PostgreSQL или session pooling. Application rate limit не заменяет ingress ограничения до аутентификации. Evidence растёт без автоматического purge: retention/backup и большие экспорты требуют планирования; completed evidence намеренно защищены от обычного удаления.
