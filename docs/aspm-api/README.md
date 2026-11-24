# ASPM API-only ingestion v1

Project — существующий DefectDojo Product. API не создаёт Products. Repository определяется парой Product + нормализованный HTTP(S) URL, Commit — Repository + полный SHA (40 или 64 hex). Scanner type — точное имя установленного штатного DefectDojo parser: например `Semgrep JSON Report` и `Trivy Scan`.

## Контракт

Все пути ниже учитывают настроенный DefectDojo URL prefix. Namespace Django: `aspm_v1`. Старые `/api/v2/` и `/api/v3/` остаются на прежних путях.

| Метод | Путь | Назначение |
|---|---|---|
| POST | `/api/aspm/v1/scans/` | Multipart-приём оригинала; 202 для новой доставки, 200 для повтора |
| GET | `/api/aspm/v1/scans/{uuid}/` | Статус собственного запуска для CI; просмотр по Product RBAC для пользователей |
| POST | `/api/aspm/v1/scans/{uuid}/retry/` | Явный retry FAILED с тем же оригиналом |
| GET | `/api/aspm/v1/scans/{uuid}/artifact/` | Авторизованное скачивание неизменённого оригинала |
| GET | `/api/aspm/v1/projects/{id}/repositories/` | Репозитории Product |
| GET | `/api/aspm/v1/repositories/{id}/commits/` | Коммиты Repository |
| GET | `/api/aspm/v1/commits/{id}/scans/` | Запуски Commit; CI видит свои запуски |
| POST | `/api/aspm/v1/commits/{id}/finalize/` | Фиксация состава, обязательный `expected_scanners` |
| POST | `/api/aspm/v1/commits/{id}/reports/` | Новая версия отчёта; optional `scan_set_id`, иначе последний finalize |
| GET | `/api/aspm/v1/commits/{id}/reports/` | История версий |
| GET | `/api/aspm/v1/reports/{uuid}/download/?format=html` | Версия HTML; `format=json` — JSON |
| GET | `/api/aspm/v1/openapi/` | OpenAPI ASPM v1 |

Списки ограничены 100 строками. Для продолжения `after` — последний repository/commit ID, UUID ScanRun или номер версии отчёта соответственно. Порядок — возрастание данного ключа. Отдельная [OpenAPI specification](openapi.yaml) генерируется из работающих DRF views; глобальная схема API v2 сохраняет свой существующий фильтр.

Обязательные multipart поля: `project_id`, `repository_id` **или** `repository_url`, `commit_sha`, `scanner_type`, `file`, `idempotency_key`. Вместо поля ключа можно использовать `Idempotency-Key` header. Если заданы оба ключа, они должны совпадать. Опционально: `branch`, `build_id`, `pipeline_id`, `job_id`, `attempt_number` (1..1000000), `scanner_version`, `scan_started`, `scan_finished`, `scan_scope`, `pipeline_url`, ожидаемый `sha256`.

Неизвестные поля отвергаются. Нельзя передать произвольный `test_id`, чужой `repository_id` или `commit_id`. URLs не загружаются платформой; repository URL — только идентификатор. Pipeline URL допускает HTTPS без credentials, query и fragment. Строки и число ожидаемых сканеров ограничены; timestamps проверяются на согласованность. Metadata описывает заявление CI и не служит доказательством авторства или времени коммита.

## Machine accounts и RBAC

SecOps выдаёт токен через CLI внутри защищённого app-контейнера:

```sh
python manage.py aspm_ingestion_token --product 17 --repository 9 \
  --user ci-project-17 --days 30 --scopes submit,status,read,finalize,reports
python manage.py aspm_ingestion_token --revoke 123
```

Новый service user получает unusable password, без staff/superuser. Для существующего пользователя это проверяется. Secret выводится один раз; хранится только SHA256 digest. Secret поместить в protected/masked CI variable `ASPM_TOKEN`. В production использовать TLS. CI передаёт `Authorization: ASPM <secret>` и никогда не использует общий SecOps token.

Scopes: `submit` — приём/retry; `status` — статус и оригинал своих запусков; `read` — чтение в разрешённом Product/Repository, включая состав финализированных отчётов; `finalize` и `reports` — отдельные разрешения оркестратора (им также нужен `read`). Для отдельных scanner jobs достаточно `submit,status`. Отзыв, expiry, active user и границы Repository проверяются на каждом запросе. Человек с session/обычным DD token может читать по Product RBAC, но не может вызывать новые мутации ASPM.

В API-only режиме обычные human member accounts также не могут обойти запрет через legacy v2/v3 import. Существующие административные интеграции superuser сохраняют штатный API. Legacy machine accounts должны быть явно enrolled выдачей действующего ASPM submit-токена тому же service user; старый формат запросов и Product RBAC остаются прежними, Git metadata не требуется. Один unusable password не считается признаком машины: это также обычный случай SSO-пользователя. ASPM scoped token не принимается legacy endpoints. CI рекомендуется только ASPM endpoint.

Лимит — `DD_ASPM_TOKEN_RATE_PER_MINUTE` (default 120 запросов в минуту), общий точный PostgreSQL counter для всех app replicas, включая status polling. По умолчанию файл не более 50 MiB (`DD_ASPM_MAX_SCAN_BYTES`): потоковая проверка при multipart-приёме, сохранении и повторная проверка в worker. Настройте ingress body/request/time limits и лимиты до аутентификации на gateway. Application rate limit начинает действовать после аутентификации.

## Idempotency и Test selection

Уникальность доставки — `(Product, idempotency_key)`. Fingerprint включает SHA256 и размер оригинала, Repository, Commit, scanner и нормализованную metadata. Одинаковая доставка возвращает тот же ScanRun без повторного импорта; другое содержимое/metadata или другой service user с тем же ключом — 409. Ключ не равен SHA256: разные job attempts с тем же файлом получают разные ScanRuns. При ротации токена того же service user ключи сохраняются.

Каждый независимый ScanRun резервирует собственные Engagement/Test в пределах Commit. Первый проход использует штатный DefaultReImporter на пустом Test. Retry частично обработанного ScanRun использует этот же Test и штатный matching/dedup. Новый commit, scanner или CI attempt всегда получает новый Test. ASPM не reimport-ит следующий commit в старый Test. Legacy import/reimport выбирает Test по старым правилам DefectDojo.

RC5 Finding write protocol и его файлы не изменены. Все записи Findings выполняются штатным importer; dedup выполняется в `sync` mode внутри фонового worker, поэтому COMPLETED ставится после фактического окончания dedup и snapshot. Session advisory lock на ScanRun исключает конкурентных workers; штатный shared Test import lock удерживается также во время snapshot. PostgreSQL row locks не удерживаются на время parsing/file I/O. Для writer нужны direct PostgreSQL или PgBouncer session mode.

## Lifecycle, outbox и сбои

`ACCEPTED → PROCESSING → COMPLETED | FAILED`. `attempt` — число запусков обработки, отдельно от CI `attempt_number`. Приём потоково сохраняет оригинал, затем в короткой DB transaction создаёт Repository/Commit/ScanRun и IngestionJob. Commit lock упорядочивает регистрацию и finalize. Отправка начинается после commit, а постоянный outbox остаётся до terminal state, даже после broker ACK.

Celery beat каждые 30 секунд вызывает dispatcher. Повторная доставка планируется через 60 секунд; живой worker защищён advisory lock. Crash после регистрации до enqueue, после broker send или при смерти worker восстанавливается из outbox. Три последовательных восстановления погибшего worker дают FAILED `worker_recovery_limit`. Parser/import failure даёт FAILED `import_failed`; чувствительный exception text не возвращается и не сохраняется. Явный retry использует тот же оригинал/Test и новую generation observations. Неполные поколения не видны UI/отчётам.

Завершённые observations содержат значения Finding, CWE, vulnerability IDs из актуального `Vulnerability` / `FindingVulnerabilityReference` (с fallback на `Finding.cve`), scanner и source ID, а не живую ссылку на Finding. Редактирование/reimport/удаление текущих Findings не меняет историю. DB constraints/triggers защищают identity, Product/Commit/Test связи, состав finalize и опубликованную историю. Удаление Product с evidence блокируется PROTECT; retention/purge требует отдельной административной процедуры.

## Оригиналы и generated reports

Приватный `DD_ASPM_ARTIFACT_ROOT` (default `/app/aspm-private`) хранит файлы под серверными UUID; client filename — только очищенная display metadata. Оригинал сохраняется побайтно, SHA256/size проверяются worker. Файлы создаются с 0600, директории evidence — 0700. Хранилище не размещать под MEDIA_ROOT/STATIC_ROOT и не публиковать nginx. Скачивание идёт только через авторизованный FileResponse, attachment, no-store, nosniff и sandbox CSP. Backup должен согласованно сохранять БД и приватный том; требуется шифрование тома/backup по политике установки. Parser/SQL logs во время ASPM import фильтруются, безопасные operational messages не содержат token/report contents.

Finalize фиксирует IDs всех принятых запусков на момент вызова. Он может включать PROCESSING/FAILED и не означает полного покрытия. POST reports фиксирует статусы и generation именно этого набора. Если не завершён хотя бы один ScanRun или отсутствует ожидаемый scanner, generated report явно INCOMPLETE. Поздний upload требует нового finalize для включения в следующую версию.

ASPM сама потоково формирует HTML и JSON из зафиксированных observations. Присланный scanner artifact никогда не становится generated report. Обе версии содержат Product, Repository, SHA, scanners, точный состав запусков, статусы, severity summary, CWE/CVE, historical observations, coverage и ссылки на оригиналы. У версии отдельные server UUID paths и checksums; новая доставка не меняет старую версию.

## UI только для просмотра

Product → Repositories → Repository → Commit → Commit evidence. Вкладки: Overview, Original Scanner Reports, ASPM Generated Reports, Historical Findings, Commit Changes. Доступ — существующий Product RBAC. Фильтр severity и сравнение двух коммитов используют сохранённые observations. Отсутствие finding при неполном покрытии не доказывает исправление. API-only режим скрывает import/reimport controls и keyboard shortcut, старые browser import routes возвращают 404 на GET и POST. Загрузка через UI отсутствует.

## Запуск и эксплуатация

```sh
docker compose -f docker-compose.yml -f docker/docker-compose.override.aspm-ingestion.yml up -d --build
docker compose exec -T uwsgi python manage.py migrate --noinput
docker compose exec -T uwsgi python manage.py check
```

Private evidence volume разделяют app и worker; nginx его не получает. Новые Django images создают mount point с UID/GID приложения и mode 0700; при использовании старого образа оператор должен предварительно инициализировать права нового тома. Celery использует штатную default queue и регистрацию dojo.tasks. Нужны worker и единственный beat. Outbox можно восстановить вручную: `python manage.py dispatch_aspm_ingestion`. Task soft/hard limits 840/900 seconds; большие отчёты должны учитывать эти лимиты. Worker resources и ingress limits нужно подобрать под используемые parsers.

Проверка схемы:

```sh
python manage.py spectacular --urlconf dojo.aspm_ingestion.schema_urls \
  --custom-settings dojo.aspm_ingestion.schema.ASPM_SCHEMA_SETTINGS --validate --fail-on-warn
```

CI examples сохраняют JSON-ответы доставки, ждут terminal states, вызывают finalize и reports с зафиксированным scan_set_id, затем потоково скачивают HTML/JSON. Для scanner jobs достаточно `submit,status`; report job использует отдельный `ASPM_REPORT_TOKEN` того же service user с `status,read,finalize,reports`. Отчёт с неполным покрытием сохраняется, а CI job завершается с кодом 2. Severity summary считает исторические observations, включая независимые повторы и duplicate flags, а не уникальные активные риски.

`queue_wait_seconds` измеряется от серверной публикации Celery задачи до начала worker; `acceptance_to_start_seconds` отдельно включает outbox/публикацию и предыдущие retries. При автоматической повторной доставке после смерти worker чистое время очереди не объявляется измеренным.

Примеры: [curl](../../examples/aspm-ci/upload.sh), [GitLab CI](../../examples/aspm-ci/gitlab-ci.yml), [GitHub Actions](../../examples/aspm-ci/github-actions.yml). Фактические результаты, ограничения измерений и release readiness — [validation.md](validation.md).
