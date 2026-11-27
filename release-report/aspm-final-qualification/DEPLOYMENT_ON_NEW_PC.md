# Развёртывание на другом ПК

Master будет доступен для этого процесса после публикации. До неё используйте этот документ как воспроизводимый порядок установки, а SHA и ветку согласуйте с отчётом о публикации.

```bash
git clone https://github.com/kaiffan/aspm-improve.git
cd aspm-improve
git switch master
git rev-parse HEAD
test "$(git rev-parse HEAD)" = "$ASPM_EXPECTED_SHA"
```

Понадобятся Linux runner подходящей архитектуры, Docker Buildx, Git, Bash, Python 3.11+ с PyYAML, Helm, kubectl, доступ к trusted registry и staging namespace. Для native AMD64 подставьте ASPM_ARCH=amd64 на AMD64 runner. Передайте reference SHA и окружение следующим инструкциям.

1. Заполните [анкету инфраструктуры](../../deploy/handover/checklists/INFRASTRUCTURE_INPUT.md).
2. Подготовьте [external PostgreSQL и CA](../../deploy/handover/docs/05_EXTERNAL_POSTGRESQL.md) и runtime Secret. Выберите [S3](../../deploy/handover/docs/19_S3_STORAGE_AND_CUTOVER.md) или filesystem/RWX.
3. Укажите [Keycloak](../../deploy/handover/docs/06_KEYCLOAK_AD_SETUP.md), TLS и роль пользователя.
4. Выполните [сборку из Git, digest publication и deploy](../../deploy/handover/docs/18_BUILD_AND_IMAGE_TRANSFER.md). Helm values находятся в [deploy/helm/aspm](../../deploy/helm/aspm) и [handover config](../../deploy/handover/config).
5. Настройте [Prometheus и VictoriaMetrics remote_write](../../deploy/handover/monitoring/README.md). Импортируйте [дашборды Grafana](../../deploy/handover/monitoring/provisioning/README.md).

После подготовки согласованных values запускайте команды из deploy/handover.

```bash
cd deploy/handover
args=(--context "$ASPM_CONTEXT" --namespace "$ASPM_NAMESPACE" --release aspm
  --profile ha --arch amd64 --chart ../helm/aspm
  -f site.yaml -f images.registry.yaml -f monitoring.site.yaml -f storage.site.yaml)
```

Передавайте массив аргументов скриптам preflight и deploy. Для smoke укажите URL staging.

```bash
scripts/preflight.sh "${args[@]}"
scripts/deploy.sh "${args[@]}" --apply
scripts/smoke-test.sh --context "$ASPM_CONTEXT" --namespace "$ASPM_NAMESPACE" \
  --release aspm --profile ha --arch amd64 --url "$ASPM_URL"
```
