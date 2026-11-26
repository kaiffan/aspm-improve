# 05 | Внешний PostgreSQL

1. DBA выделяет чистую БД и роль с правом менять её схему. В лаборатории использован PostgreSQL 18.6. Встроенный migration hook использует тот же `database-url`, что и приложение. Разделение ролей требует корпоративного процесса миграций и квалификации.
2. Поместите PostgreSQL URI в Secret `existingSecret` под ключом `secretKeys.databaseUrl`. Кодируйте специальные символы credentials по правилам URI. FQDN совпадает с сертификатом. Для session advisory locks настройте прямой доступ к primary или session pooling.
3. `databaseTLS.existingSecret` указывает Secret с `ca.crt`. `config.DD_DATABASE_OPTIONS` — строка JSON `{"connect_timeout":5,"sslmode":"verify-full","sslrootcert":"/app/db-tls/ca.crt"}`. `config.DD_DATABASE_CONN_MAX_AGE` по умолчанию 60 с. `networkPolicy.egress` разрешает private PostgreSQL CIDR/5432 и зависимости.
4. Проверьте SQL из preflight и итог migration hook. DBA сверяет слоты, WAL, I/O, slow queries и `idle in transaction`.

```sql
SHOW max_connections;
SELECT state, wait_event_type, count(*)
FROM pg_stat_activity WHERE datname = current_database() GROUP BY 1, 2;
SELECT ssl, version FROM pg_stat_ssl WHERE pid = pg_backend_pid();
```

В staging испытайте reconnect и release блокировок при failover. В `config/values-external-db.example.yaml` замените адрес TEST-NET и добавьте egress остальных зависимостей.
