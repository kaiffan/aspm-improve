# 04 | Установка Standard HA с нуля

1. Проверьте архив по [START_HERE](../START_HERE.md). Заполните [таблицу параметров](../checklists/INFRASTRUCTURE_INPUT.md), назначьте ответственных и окно работ. Подготовьте staging namespace, RBAC, квоты и проверенные Linux-образы нужной архитектуры.
2. Получите images.registry.yaml по [инструкции сборки и публикации](18_BUILD_AND_IMAGE_TRANSFER.md). Скопируйте `config/values-production.example.yaml` в `site.yaml`. Заполните поля окружения из анкеты. Передайте images.registry.yaml после site.yaml, чтобы применить digests и исходную ревизию образов из вашего registry. Соберите всю egress конфигурацию в один список. Helm заменяет списки при наложении файлов.
3. Через корпоративный secret controller создайте runtime Secret, CA для PostgreSQL, OIDC client Secret, registry pull secret при необходимости и Ingress TLS Secret. `config/runtime-secret.example.yaml` показывает ключи. Пароли, URI с credentials и private keys передавайте через штатный secret store.
4. Provision: выделенные PostgreSQL DB и role, независимые broker/cache endpoints, два RWX PVC, DNS и NetworkPolicy. Настройте права UID 1001, GID 1337. [DB](05_EXTERNAL_POSTGRESQL.md) · [CSI](07_STORAGE_CONFIGURATION.md) · [Сеть](08_NETWORK_AND_TLS.md)
5. Выполните команды в корне комплекта. Заполните переменные из анкеты.

```bash
test -n "$ASPM_CONTEXT" && test -n "$ASPM_NAMESPACE" && test -n "$ASPM_ARCH"
scripts/preflight.sh --context "$ASPM_CONTEXT" --namespace "$ASPM_NAMESPACE" \
  --release aspm --profile ha --arch "$ASPM_ARCH" -f site.yaml -f images.registry.yaml
scripts/deploy.sh --context "$ASPM_CONTEXT" --namespace "$ASPM_NAMESPACE" \
  --release aspm --profile ha --arch "$ASPM_ARCH" -f site.yaml -f images.registry.yaml --apply
```

Для мониторинга добавьте согласованный overlay через дополнительный -f после images.registry.yaml. Preflight проверяет узлы, PVC и ключи Secret, рендер Helm и server dry run. Диагностический Pod проверяет SQL, broker/cache PING, discovery IdP и запись на тома. Запуск контейнеров подтверждает доступ к обоим образам. В кластере с default-deny заранее согласуйте доступ migration hook и диагностического Pod к зависимостям.

Deploy ждёт `Migration Job: Succeeded`, Ready web/worker/Beat, три HTTP 200 health, Helm test и `Login HTTP 200`. Подготовьте [bootstrap-аккаунт](09_ADMIN_GUIDE.md), проверьте [Keycloak](06_KEYCLOAK_AD_SETUP.md) и завершите [чеклист](../checklists/POST_DEPLOYMENT.md). Запишите Helm revision, chart version и registry manifests.

При отказе проверьте предыдущий вывод, события и Job по [runbook](16_TROUBLESHOOTING.md). `--apply` разрешает install/upgrade выбранной цели. Default timeout — 35 минут.
