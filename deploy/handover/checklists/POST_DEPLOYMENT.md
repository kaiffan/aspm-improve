# Чеклист после развёртывания

- [ ] Записаны Helm revision, успешный migration hook, app SHA, реальные image IDs и signatures.
- [ ] Web, workers, Beat Ready. Runtime SQL/Redis/storage, health, Helm test, DNS/TLS и browser login прошли.
- [ ] Проверены Classic import/reimport и Finding triage в тестовом проекте.
- [ ] Проверены scoped CI upload, статус COMPLETED, SHA-256 оригинала и обе выгрузки, действует RBAC.
- [ ] Проверены Keycloak login, revoke, выход, профиль Expert/SecOps, оба User направления и отсутствующие grants.
- [ ] Проверена тестовая доставка webhook, ротация, monitoring alerts, backup и отдельное восстановление.
- [ ] Занесены результаты в release gate. Выпуск согласован владельцем.
