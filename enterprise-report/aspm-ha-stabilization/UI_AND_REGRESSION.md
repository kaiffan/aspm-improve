# Интерфейс и регрессия кандидата

SHA приложения `eee10e678c77480deceb794da92a1bc660cd0dee`. Единственная правка приложения добавляет доступное имя кнопке закрытия диалога о завершении сессии и явно задаёт тип кнопки. Glyph скрыт от assistive technology, имя локализуется. Chromium проверил видимость диалога и закрытие по Enter на всех восьми ширинах. Корпоративная палитра и структура экранов сохранены. [Шаблон](../../dojo/templates/base.html) · [Диалог, 320 px](screenshots/after-session-dialog-320.png)

## Браузер

Playwright/Chromium проверил 208 состояний страниц без переполнения документа, 36 действий и шесть профилей Keycloak. 13 маршрутов × 8 ширин × 2 палитры дали по 104 состояния Light и Dark. System отдельно переключал системное предпочтение Light и Dark на каждой ширине. Проверены 320, 360, 390, 768, 1024, 1280, 1440 и 1920 px, disclosure клавиатурой и указателем, горизонтальная прокрутка длинных таблиц, фильтры и пустое состояние, переходы между workflow, скачивание артефакта и HTML Classic Report viewer. Проверка использовала синтетические данные. Во всех 208 состояниях загружена таблица стилей с SHA `eee10e678c77`.

Пять пар цветов прошли целевые пороги в обеих палитрах. Контраст обычного текста 15,20:1 / 14,06:1, приглушённого 6,33:1 / 8,88:1, боковой навигации 13,61:1, выделенного пункта 13,20:1. Контраст focus indicator 6,80:1 / 7,23:1. Покрытие ограничено проверенными сочетаниями и Chromium.

| Роль | Проверенный результат |
|---|---|
| SecOps | 8 синтетических проектов, Findings и настройки HTTP 200 |
| Expert | 8 проектов и Findings HTTP 200, настройки HTTP 403 |
| User | Ровно 0, 1 TEST, 1 PAYMENTS или 2 проекта в четырёх выборках grants. Общий Findings и настройки HTTP 403 |

[Данные Chromium](raw/browser-after.json) · [DevSecOps Dark, 390 px](screenshots/after-commit-390-dark.png) · [Classic, 1440 px](screenshots/after-classic-1440.png) · [Фильтры Findings Dark, 390 px](screenshots/after-findings-390-dark.png) · [HTML Classic Report, 1920 px](screenshots/after-classic-report-viewer-1920.png) · [SecOps](screenshots/after-secops-390.png) · [Expert](screenshots/after-expert-390.png) · [User](screenshots/after-reader-test-390.png)

## Регрессия

| Набор | Результат | Артефакт |
|---|---|---|
| Django | 8 909 всего, 8 356 прошли, 553 ожидаемых пропуска, 0 fail/error. Четыре свежих test DB. Полный набор ID совпадает с прежним последовательным прогоном | [Сводка](raw/django-final-summary.txt) |
| JavaScript | 17 прошли | [Журнал](raw/javascript.txt) |
| Helm | 19 unit tests, lint, strict server dry run и живой Helm smoke | [Unit](raw/helm-unit.txt) · [Lint](raw/helm-lint-production.txt) · [Strict](raw/final-server-validation.txt) · [Live](raw/helm-test-final.txt) |
| Browser и Keycloak | 208 состояний, 36 действий, 6 профилей, 0 ошибок | [Сводка](raw/browser-summary.json) |
| Django strict | 85/85 с `ASPM_TEST_API_ONLY=True` в отдельной тестовой БД. Включает реальные подписи/HTTP через тестовый TLS-приёмник | [Сводка](raw/django-strict-summary.txt) |
| Keycloak revoke | Следующий вход без доступа. Существующая сессия получила HTTP 403 через 119,31 с при TTL 120 с. Прежние тестовые права восстановлены | [Журнал](raw/keycloak-revocation.json) |
| Django live | System check, `makemigrations --check --dry-run`, миграции не требуются | [Результат](raw/django-live-checks.txt) |
| OpenAPI | v2 побайтово совпал с исходным SHA-256. v3 структурно совпал после исключения `servers`, 41 path. TLS-схема ASPM вернула 11 path | [Результат](raw/openapi-final.txt) |
| Webhooks | Live queue, фильтр severity, повторы и replay в одинаковый delivery, scoped management. Тестовый внешний hostname зарезервирован и завершился ожидаемым DNS failure. Отдельный strict тест подтвердил HTTP, сертификат и HMAC на тестовом TLS-приёмнике | [Live](raw/webhook-final.json) · [Strict TLS](raw/django-strict-summary.txt) |
| Classic / DevSecOps и Finding concurrency | Live Classic import и reimport HTTP 201 для одного Test, один Finding, конкурентный PATCH сохранился. Параллельные DevSecOps ScanRun и report завершились, Classic engagement сохранил отсутствие SCM context | [Смешанный workload](raw/mixed-final.json) |
| Zero-Finalize / immutable reports / RWX | Три отчёта после worker drills без Finalize. Хеши оригинала и отчёта на обеих web-репликах совпали. SHA-256 опубликованного отчёта совпал после изменения Finding | [RWX](raw/shared-storage-final.json) · [PATCH и отчёт](raw/immutable-final.json) |
