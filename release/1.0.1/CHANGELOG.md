# ASPM 1.0.1

27 ноября 2026 года. Ревизия приложения для сборки образов `e2f3f244f478033f5137ccb1248ab9c3b5d577df`, Helm Chart `0.1.0-rc.11`, база DefectDojo OSS 3.5.100. Публикация в `master` предназначена для тестового развёртывания. [Паспорт поставки](../../deploy/handover/DELIVERY_MANIFEST.json)

## CI/CD и отчёты

- Добавили `POST /api/aspm/v1/scans/` для загрузки результатов CI с токеном конкретного проекта. Скан связывается с Product, Repository, Commit и настроенным Engagement. Повтор идентичного запроса с тем же ключом идемпотентности возвращает ранее принятый результат.
- Добавили обработку через outbox и Celery. Страница коммита показывает принятый скан до завершения разбора. После обработки система формирует версии HTML- и JSON-отчётов без отдельного запроса на финализацию.
- Сохранили ручной импорт и повторный импорт в Classic. Для CI предусмотрен профиль API-only. Добавили историю запусков, просмотр сканов и сравнение результатов по коммитам.
- Проверили сквозную загрузку и выгрузку для Dependency-Track FPF, Semgrep JSON, Trivy, KICS, Fortify XML и ffuf. [Матрица форматов](../../release-report/aspm-final-qualification/SCANNER_COMPATIBILITY.md)

## Интерфейс, доступ и интеграции

- Обновили навигацию Classic, DevSecOps и администрирования, логин, Dashboard и страницы результатов. Добавили переключение светлой, тёмной и системной темы и адаптивные таблицы.
- Улучшили клавиатурную навигацию, подписи полей и элементов форм. На узких экранах таблицы в деталях Finding прокручиваются внутри своей области.
- Добавили вход через Keycloak, настройку ролей и разграничение доступа к результатам и диагностике по проектам.
- Добавили исходящие вебхуки с подписанными запросами, очередью, повторными попытками и историей доставки. Управление вебхуками ограничено правами пользователя.

## Производительность и корректность

- Оптимизировали SQL для сводок Dashboard, Product и Finding, а также страницы коммита. Сократили лишние выборки и загрузку связанных объектов.
- Исправили стабильность сортировки и пагинации, точные счётчики при фильтрации по связанным объектам и сброс фильтров.
- Уточнили границы транзакций при конкурентной записи Findings. Вызовы интеграций и постановка пересчёта Product Grade выполняются после освобождения блокировок или подтверждения записи, в зависимости от операции.

## Развёртывание, хранение и эксплуатация

- Добавили Helm-профили для локальной установки и HA с внешними PostgreSQL и Valkey. Миграции запускаются отдельной Job. Миграционные и тестовые хуки учитывают правила размещения на узлах.
- Добавили приватное S3-хранилище оригиналов сканов, отчётов и Classic media, файловый профиль и RWX. Документировали перенос, резервное копирование PostgreSQL и файлов, восстановление и сверку контрольных сумм.
- Добавили повтор временных ошибок хранения, Scan Processing и System Health. При неверной конфигурации приватного хранилища API сообщает о недоступности, а диагностика показывает проблемную зависимость.
- Добавили сбор метрик Prometheus, передачу метрик в VictoriaMetrics, дашборды Grafana и проверки оповещений.
- Подготовили сборку из проверенного SHA, проверку digest в registry, инструкции по установке на другой машине и план отката. [Начало работы](../../deploy/handover/START_HERE.md)

## Безопасность и квалификация

- Удалили неиспользуемый XMLSec и системный `libxml2` с CVE-2026-6653 из Debian runtime. Проверили обработку XML через `lxml`.
- Убрали `pip` и `ensurepip` из Django runtime. Обновили `setuptools` до 84.2.1. Повторный Trivy-скан образов показал 0 критических находок и 0 секретов. В системных пакетах Debian остаются 56 находок HIGH без указанных в базе сканера исправленных версий. [Отчёт по безопасности](../../release-report/aspm-final-qualification/SECURITY_REPORT.md)
- После исправлений безопасности прошли 8 349 тестов Django, 562 были пропущены. Падений нет. JavaScript прошёл 17/17, Helm 23/23. Пройдены чистые миграции и проверка запуска на Linux/ARM64. Отдельная проверка хранилища прошла 9 сценариев на MinIO. [Регрессия](../../release-report/aspm-final-qualification/FINAL_REGRESSION.md)
- Production остаётся **HOLD**. Открыты многонодовый HA, профиль native AMD64, корпоративные зависимости и полный Ruff. В GitHub CI на исходной публикации прошёл Migration Graph, а Ruff Linter и Setup Pages завершились ошибкой. [Условия выпуска](../../release-report/aspm-final-qualification/RELEASE_GATE.md) · [Ограничения](../../release-report/aspm-final-qualification/KNOWN_LIMITATIONS.md)

## История кандидатов

### ASPM 1.0.1 RC2

- Restore native Clear navigation without changing Product filtering or permissions.
- Preserve primary UI ordering with a PK tie-break; bound user page size and recover malformed values.
- Use standard DRF pagination for collection/delete-preview lists; retain opt-in FAST ORM path.
- Label late-initialized Select2 combobox/search controls from existing labels.
- Isolate the test-only grade cache marker; keep exact query assertions unchanged; make offline Jira DNS failure matching portable.
- Freeze source/build metadata and repeat controlled R5/RC1/RC2 benchmarks and real browser/import/rollback checks. Formal promotion blocked by two inherited loader errors.

The RC1 changelog below is historical.

### ASPM 1.0.1 RC1

- Added: shared OTP-derived design tokens without the excluded light-blue accent; original ASPM SVG identity and replaceable branding.
- Added: Light/Dark/System with persistent browser preference, live chart colors, accessible mobile shell and focus behavior.
- Improved: Dashboard hierarchy/numeric formatting, dense tables, form/editor/filter/report/login themes, page-size menu positioning, accessible names/contrast and asynchronous Tagulous labeling.
- Removed from UI: commercial purchase/PAYG/Pro menus, promotional OS/star/error/long-request banners. Operator/read-only messages and upstream legal attribution retained.
- Added: separate product/upstream/source metadata, standalone report generator/cover branding and digest-pinned reproducible app/nginx builds.
- Preserved: all Round1–5 application optimizations and standard API/authorization/import/deduplication behavior. No new migrations/indexes/services/cache layer.
- Verified: repeated HTTP and browser comparisons, real write/import gates, source/translation hashes and real rollback. Known inherited pagination/status limitations remain explicit; no stable production tag.

Measured results and complete scope: RELEASE_NOTES.md, PERFORMANCE.md, TEST_RESULTS.md.
