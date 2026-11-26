# Регрессии и совместимость

Строгий Django прогон прошёл 85 тестов. В него вошли Zero-Finalize, роли и гранты, Classic workflow и сохранность storage. Первичный полный прогон нашёл три изменения видимых статусных подписей. Они исправлены с сохранением как компонента, так и канонического текста. При параллельном повторе Django runner не сериализовал TextIOWrapper, затем проверка продолжилась через последовательный запуск. На переиспользованной тестовой среде восемь точных проверок SQL-count дали расхождения. Повторный чистый прогон прошёл. В четырёх отдельных тестовых БД и кешах выполнены те же 8 909 тестов, что и при полном последовательном обнаружении. Итог — 8 356 PASS, 553 унаследованных пропуска, 0 падений.

Финальная браузерная матрица прошла 208 загрузок, 27 взаимодействий и шесть OIDC аккаунтов. Проверены портфели Product, клавиатурная навигация, скачивание scanner report через TLS и доступные границы ширины.

JavaScript прошёл 17 тестов. Helm прошёл 19 render/schema tests, линт для трёх профилей, server-side strict dry run и живой helm test. Django check и makemigrations --check завершились, миграции не требуются. Тестовый образ сообщает унаследованный staticfiles.W004 о node_modules, фактический nginx отдаёт собранные байты CSS/JS с проверенным SHA.

OpenAPI v2 байтово совпал с базовым. Структура v3 и 41 путь совпали после исключения URL сервера. Контракт ASPM ingestion получен через рабочий TLS. Бэкап лабораторной БД восстановлен в PostgreSQL 18.6 без сети. Пять счётчиков таблиц совпали. Через Ingress успешно принят и обработан синтетический отчёт размером 48 MiB.

[Строгий suite](raw/django-strict-final-summary.txt) · [Полный suite](raw/django-final-summary.txt) · [Состав групп](raw/django-clean-modules.json) · [Результат повторного использования среды](raw/django-reused-db-summary.txt) · [JavaScript](raw/javascript.txt) · [Helm](raw/helm-unittest.txt) · [Live helm test](raw/helm-test-final.txt) · [Backup](raw/backup-restore.txt) · [OpenAPI](raw/openapi-validation.txt) · [Upload](raw/large-upload.txt)

Webhook smoke прошёл на новом синтетическом проекте. Две попытки доставки завершились ожидаемой ошибкой DNS на зарезервированном адресе. Replay сохранил идентификатор и четыре попытки. Тесты TLS/HMAC пройдены отдельно в строгом Django suite. [Webhook evidence](raw/webhook-smoke.json)
