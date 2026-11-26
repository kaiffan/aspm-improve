# Данные от владельцев корпоративной инфраструктуры

- PostgreSQL primary DNS, порт, база, пользователь, пароль через Secret, private CA, connection budget и backup policy.
- Registry, pull credentials, digest образов для целевой архитектуры.
- Отдельные broker/cache, TLS, credentials, persistence и rotation.
- StorageClass с RWX, размеры, UID/GID, encryption, backup и retention.
- ASPM hostname, IngressClass, TLS Secret, доверенные заголовки, лимиты upload и timeouts.
- Keycloak issuer и realm, client ID, client Secret, callback и redirect, AD claims и гранты Product.
- Nodes, зоны, workload quotas, Metrics API, мониторинг и согласованные SLO/RPO/RTO.
- Разрешённые интеграции, egress CIDR и webhook receivers.

[Рабочий пример PostgreSQL](raw/profile-external-postgresql.yaml) · [DB budget](DATABASE_CONNECTION_BUDGET.md)
