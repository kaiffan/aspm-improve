# Данные для первого развёртывания ASPM с внешней PostgreSQL

Заполните последний столбец. Имена Secret и ключей можно передать вместе с остальными параметрами. Пароли, полные URI и значения токенов передайте через менеджер секретов.

## PostgreSQL

ASPM Chart не содержит PostgreSQL subchart, StatefulSet или переключатель для bundled PostgreSQL. В OrbStack отдельный PostgreSQL развёрнут лабораторным манифестом. Для внешней БД используйте новый release или namespace и применяйте ASPM Chart с [примером values](../deploy/helm/aspm/values-external-postgresql.example.yaml).

| Parameter | Required | Default | Actual Helm values path | My value |
|---|---|---|---|---|
| PostgreSQL hostname | Yes | — | Host в URI из `existingSecret` → `secretKeys.databaseUrl` | |
| PostgreSQL port | Yes | 5432 (PostgreSQL) | Port в том же URI, плюс `networkPolicy.egress[].ports[].port` | |
| Database name | Yes | — | Database в том же URI | |
| Database username | Yes | — | Username в том же URI | |
| Existing Secret name | Yes | `aspm-runtime` | `existingSecret` | |
| Password Secret key | Yes | `database-url` для полного URI | `secretKeys.databaseUrl` | |
| SSL mode | Yes | `verify-full` | JSON-поле `sslmode` в `config.DD_DATABASE_OPTIONS` | |
| CA certificate Secret | Yes для профиля примера | `aspm-postgres-ca`, ключ `ca.crt` | `databaseTLS.existingSecret`, JSON-поле `sslrootcert` в `config.DD_DATABASE_OPTIONS` | |
| Connection timeout | Yes | 5 с в примере, 3 с в базовом Chart | JSON-поле `connect_timeout` в `config.DD_DATABASE_OPTIONS` | |
| Connection lifetime | Optional | 60 с | `config.DD_DATABASE_CONN_MAX_AGE` | |
| PostgreSQL version | For validation | Лаборатория использует PostgreSQL 18 | — | |
| Connection pooler | Optional | Direct primary | Endpoint в URI, указанном через `existingSecret` и `secretKeys.databaseUrl` | |
| PostgreSQL private endpoint CIDR | Yes при NetworkPolicy | — | `networkPolicy.egress[].to[].ipBlock.cidr` | |

`secretKeys.databaseUrl` указывает на ключ с URI `postgresql://USER:PASSWORD@HOST:PORT/DATABASE`. Закодируйте спецсимволы отдельно в имени пользователя и пароле с помощью percent-encoding. Поддерживаемый Chart не читает отдельный ключ с паролем. Migration Job, init-контейнеры и Django web, worker и beat получают одну ссылку на Secret, одинаковые опции подключения и CA. Django считывает URI из `DD_DATABASE_URL`.

ASPM использует PostgreSQL advisory locks уровня сессии для миграций, beat и обработки ScanRuns. Для первого запуска нужен прямой endpoint primary. Внешний pooler допускается в режиме session pooling после проверки блокировок, reconnect и failover. Зависимости приложения содержат `psycopg[c]`. Встроенный Django pool требует дополнительный пакет `psycopg_pool` и `CONN_MAX_AGE=0`. [Настройки Django 5.2](https://docs.djangoproject.com/en/5.2/ref/databases/) · [Параметры libpq](https://www.postgresql.org/docs/18/libpq-connect.html)

## Права и подключение

1. DBA заранее создаёт отдельную пустую БД ASPM. Для конфигурации с одной ролью выделите владельца этой БД и схемы `public`, без полномочий SUPERUSER, CREATEROLE или CREATEDB. Проверьте `CONNECT` к БД, `USAGE` и `CREATE` в целевой схеме; миграции должны владеть создаваемыми таблицами, индексами, последовательностями, функциями и триггерами и уметь их изменить.
2. Миграция `0278_global_search_fts_trigram_indexes` использует встроенное расширение `pg_trgm`. У провайдера оно должно быть доступно. DBA может заранее создать его в выделенной базе, если инициализация расширений ограничена. Django также использует обычные DDL и `plpgsql` для триггеров; проверьте, что стандартный язык доступен. [Миграция](../dojo/db_migrations/0278_global_search_fts_trigram_indexes.py) · [Документация PostgreSQL](https://www.postgresql.org/docs/18/pgtrgm.html)
3. При единой роли runtime получает права через владение объектами. Если требуется отдельный runtime principal, понадобятся `CONNECT`, `USAGE` на схему, `SELECT, INSERT, UPDATE, DELETE` на рабочие таблицы, `USAGE, SELECT` на последовательности, `EXECUTE` там, где нужны функции, и соответствующие default privileges для будущих объектов. Раздельные учётные данные migration/runtime требуют отдельного изменения контракта Chart.
4. Настройте DNS для Pod, исходящий TCP к указанному PostgreSQL-порту, allowlist на firewall и `pg_hba.conf` с фактическим источником egress кластера. Сертификат должен совпадать с FQDN в URI. Откройте egress к broker/cache и, при включении, Keycloak и согласованным webhook endpoints. Helm заменяет списки целиком: объедините все правила в одном итоговом `networkPolicy.egress`.
5. До миграции запустите одноразовый Pod в согласованном namespace с теми же selector labels, CA mount и `secretKeyRef`, что у Migration Job. Из него выполните `python manage.py shell` и SQL ниже через `django.db.connection.cursor()`. Для разделения DNS/TCP и TLS ошибки можно предварительно вызвать `pg_isready -h HOST -p PORT`; проверка `pg_isready` сама по себе не подтверждает TLS или права. Сверьте имя, роль, версию, `pg_is_in_recovery()=false`, параметры TLS и пустоту базы с владельцем до запуска Helm.

```sql
SELECT current_database(), current_user, current_setting('server_version'),
       pg_is_in_recovery();
SELECT ssl, version, cipher FROM pg_stat_ssl WHERE pid = pg_backend_pid();
SELECT has_database_privilege(current_database(), 'CONNECT'),
       has_schema_privilege('public', 'USAGE'),
       has_schema_privilege('public', 'CREATE');
SELECT schemaname, tablename FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename;
SELECT name, default_version, installed_version FROM pg_available_extensions
WHERE name IN ('pg_trgm', 'plpgsql');
```

Для подтверждённой пустой БД проверьте право создать таблицу и функцию в транзакции с `ROLLBACK`. Перед bootstrap согласуйте резервное копирование и бюджет подключений с DBA. Если нужно квалифицировать root-squashed RWX, используйте отдельную копию среды.

## Kubernetes и сопряжённые службы

| Этап | Параметры для заполнения | Helm values или ресурс |
|---|---|---|
| Первый запуск | Context ______ · Namespace ______ · release name ______ | `--kube-context`, `--namespace`, имя release |
| Первый запуск | Registry и digest Django ______ · Registry и digest nginx ______ · ImagePullSecret ______ | `image.repository`, `image.digest`, `nginxImage.repository`, `nginxImage.digest`, `imagePullSecrets` |
| Первый запуск | StorageClass ______ · evidence PVC ______ · media PVC ______ | PVC создаются отдельно. `storage.existingClaim`, `storage.mediaExistingClaim`, `storage.minimumFreeBytes` |
| Первый запуск | Valkey/Redis broker endpoint ______ · cache endpoint ______ · TLS/ACL ______ · CIDR ______ | `secretKeys.brokerUrl`, `secretKeys.cacheUrl`, `networkPolicy.egress` |
| Первый запуск в браузере | Публичный URL ______ · Ingress hostname ______ · class ______ · TLS Secret ______ | `config.DD_SITE_URL`, `config.DD_ALLOWED_HOSTS`, `ingress.enabled`, `ingress.host`, `ingress.className`, `ingress.tlsSecretName`. Для изолированного smoke возможен port-forward. |
| Корпоративный SSO | Issuer ______ · HTTPS callback ______ · client ID ______ · имя/ключ Secret ______ · IdP CA Secret ______ · группы и роли ______ | `oidc.issuer`, `oidc.callbackUrl`, `oidc.clientId`, `oidc.existingSecret`, `oidc.clientSecretKey`, `oidc.existingCaSecret`, `oidc.roleClaim`, `oidc.groupClaim` |
| Staging qualification | Реальный CSI и RWX ______ · backup/restore и retention ______ · webhook consumer allowlist ______ · лимиты/квоты ______ · профиль нагрузки ______ | PVC/StorageClass, ресурсы `web`/`worker`/`beat`, `networkPolicy.egress`, эксплуатационные параметры инфраструктуры |
| Опционально | HPA ______ · Prometheus ______ · pooler в режиме session ______ | `hpa.enabled`, `monitoring.serviceMonitor.enabled`, URI в Secret |

## Secret references

- Основной runtime Secret с пятью ключами. [Пример без рабочих значений](aspm-runtime-secret.example.yaml)
- PostgreSQL CA Secret с `ca.crt`. [Пример](aspm-postgres-ca-secret.example.yaml)
- Registry pull, ingress TLS и Keycloak client Secret по необходимости. Для Keycloak используйте отдельный Secret, который Chart монтирует только в web.

Создайте Secret через утверждённый менеджер или из защищённых локальных файлов с помощью `kubectl create secret generic ... --from-file=KEY=/secure/PATH` в целевом namespace. Проверьте имена объектов и наличие ожидаемых ключей без вывода значений. Пароли и URL с паролями не передаются через `--set`, значения Helm или артефакты.

После получения ответов сначала подтвердите целевой context/namespace, TLS, версию, права и пустую БД. Выполните migration Job и дождитесь web, worker и beat. Затем выполните Helm ClusterIP smoke и проверки браузера, Classic import/reimport, DevSecOps Zero-Finalize, отчётов, вебхуков и сохранности файлов после restart с небольшими синтетическими данными. Для квалификации на миллионе Findings нужен отдельный стенд.
