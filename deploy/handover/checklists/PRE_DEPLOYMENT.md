# Чеклист до развёртывания

- [ ] Сверены SHA256SUMS, application SHA, arch и registry digests, проверены SBOM и принятые security findings.
- [ ] Утверждён staging context, namespace, release и окно изменений. Доступы RBAC и журналирование готовы.
- [ ] Внешние PostgreSQL, broker/cache, Keycloak и private DNS подтверждены владельцами.
- [ ] Созданы CA и Secret references, TLS на ingress, два RWX claim, верные filesystem permissions и capacity reserve.
- [ ] Заполнен единый values overlay. Проверены egress, route, PDB/placement, квоты и запас под rollout.
- [ ] Согласованы RPO/RTO, backup, schema-review для upgrade/rollback, контактные роли.
- [ ] Preflight на выбранном target завершился с кодом 0.
