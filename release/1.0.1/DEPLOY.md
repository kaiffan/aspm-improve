# Запуск кандидата

Локальный RC проверяется на **48086**, на БД **aspm_rc1_validation**. Старое приложение на 8080 и исходная БД не заменяются. Приватный стендовый Compose/env хранятся вне Git. Публичный `compose.yaml` — воспроизводимый рецепт для уже настроенных внешних PostgreSQL и broker/cache; он не создаёт и не удаляет БД.

1. Сохранить текущие image IDs, конфигурацию, backup PostgreSQL и media; проверить восстановление backup отдельно. Не выполнять `down -v`.
2. Собрать/загрузить закреплённые RC-образы по BUILD.md. Подготовить приватный файл по runtime.env.example, режим 0600. Заполнить SECRET_KEY, реальные внешние адреса, hosts, SITE_URL, учётные данные. На существующей БД сохранить точный DD_CREDENTIAL_AES_256_KEY: произвольная замена делает сохранённые tool passwords нечитаемыми. Изменение ключей требует отдельного плана; стендовые ключи не менялись. Примерные значения не являются рабочими секретами.
3. Указать `ASPM_RUNTIME_ENV` (абсолютный путь), `ASPM_MEDIA_VOLUME` (существующий media volume), при необходимости ASPM_PORT. Все три настройки — параметры Compose, не секретный файл в репозитории. Перед запуском проверить, что внешний PG/broker доступны из Docker network.
4. Выполнить check и проверку состояния миграций. Этот RC не содержит новых миграций; не запускать initializer поверх существующей БД автоматически.

```sh
docker compose -f release/1.0.1/compose.yaml run --rm --no-deps \
  --entrypoint python aspm manage.py check
docker compose -f release/1.0.1/compose.yaml run --rm --no-deps \
  --entrypoint python aspm manage.py makemigrations --check --dry-run
docker compose -f release/1.0.1/compose.yaml up -d aspm nginx
```

5. Проверить `/login?force_login_form`, обе темы, CSS/SVG/JS MIME, API с ограниченной учётной записью, exact count, фильтры, порядок. Тему проверить в новом browser profile: System по умолчанию.
6. До включения `--profile background up -d worker` убедиться, что broker/cache/media и БД принадлежат одному окружению. Для отдельной проверки используются отдельные очереди и копия БД. Scheduler включается отдельно через профиль scheduler; никогда не запускать два beat для одного окружения. Одновременные конфликтующие версии приложения/worker на общей БД не допускаются.

Gateway по умолчанию привязан к loopback. Для внешней эксплуатации нужны TLS/reverse proxy, корректные secure cookies/CSRF origins, секреты, мониторинг, backup/restore, внешняя HA PostgreSQL и проверка ёмкости. Эти эксплуатационные требования не подтверждены локальным RC-тестом. Не копировать benchmark middleware, private account/session files или DEBUG-настройки в deployment.

Brand name/mark/favicon заменяются DD_ASPM_BRAND_NAME/DD_ASPM_BRAND_MARK/DD_ASPM_FAVICON. Пути только относительно локального static, без URL и `..`. Передать одинаковые статические файлы в app/nginx-образы; permissions и API от брендинга не зависят.

Для локальных PG/Valkey в уже существующей Docker network добавить `-f release/1.0.1/compose.local.yaml` к командам Compose и указать ASPM_DOCKER_NETWORK. Это не требуется для внешних достижимых DNS-адресов. При проверке второй копии выбрать свободный loopback ASPM_PORT; не запускать второй worker/beat той же очереди. Health probe использует разрешённый Host из DD_ALLOWED_HOSTS и не требует открытого wildcard. Публичный рецепт дополнительно проверяется отдельным проектом на48090 без worker/beat/initializer, затем останавливается.
