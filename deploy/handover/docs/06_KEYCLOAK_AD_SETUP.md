# 06 | Keycloak и AD

1. IAM настраивает LDAP/AD federation, синхронизацию групп и политику отключённых учётных записей. Подготовьте staging realm и группы TEST/PAYMENTS.
2. Зарегистрируйте confidential OIDC client. Включите Authorization Code, PKCE S256. Точный redirect — `https://ASPM_HOST/sso/callback`. Для RP-initiated logout зарегистрируйте `https://ASPM_HOST/login`.
3. Укажите `oidc.issuer` (полный HTTPS realm URL), `oidc.clientId`, `oidc.callbackUrl` и `oidc.existingSecret`. Default key `oidc-client-secret`. Для частного CA передайте `oidc.existingCaSecret` с `ca.crt` и установите доверие в браузерах.
4. Настройте ID token claims. Default role claim `aspm_roles`, group claim `aspm_product_grants`. Сопоставьте группы со стабильными проектами в Access Management. Сохраните владельца каждого mapping.
5. Проверьте вход, claims по redacted IdP audit, выход, refresh/revoke на активной сессии. По умолчанию `oidc.sessionAge=3600`, `oidc.groupTtl=300` секунд. Сверьте TTL с IAM.

| Субъект | Ожидание |
|---|---|
| User TEST, PAYMENTS, оба, пустые grants | Ровно соответствующие проекты в обоих пространствах. Лишние объекты и выгрузки отклоняются |
| Expert | Projects, Findings, отчёты, triage и False Positive. Административные страницы закрыты |
| SecOps | Системные настройки и проекты в пределах утверждённой модели |
| Отключённый или отозванный | Новый вход отклонён или лишён соответствующих прав. Активная сессия обновляет доступ в согласованный срок |

Для corporate gate подтвердите реальные AD группы, SSO/TLS, ротацию и отказ внешнего IdP.
