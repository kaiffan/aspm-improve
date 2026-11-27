# ASPM 1.0.1 | Начало работы

ASPM 1.0.1 объединяет классическое управление уязвимостями DefectDojo и приём результатов CI/CD с привязкой к репозиторию и коммиту. Текущий Helm Chart — `0.1.0-rc.11`. Ревизию приложения и версии компонентов указывает [паспорт поставки](DELIVERY_MANIFEST.json).

Production остаётся **HOLD**. Для staging выберите профиль S3 или filesystem/RWX. При переносе существующих файлов на S3 запланируйте окно остановки записи и сверку контрольных сумм.

[Переход на S3](docs/19_S3_STORAGE_AND_CUTOVER.md) · [Консистентная резервная копия](docs/14_BACKUP_RESTORE.md) · [Квалификация rc.11](qualification/FINAL_STORAGE.md)

## Порядок установки

1. Получите проверенный checkout из Git или распакуйте Enterprise Delivery Package. [Команды получения и проверки файлов](docs/18_BUILD_AND_IMAGE_TRANSFER.md).
2. Заполните [анкету инфраструктуры](checklists/INFRASTRUCTURE_INPUT.md). Для корпоративного staging подготовьте registry, namespace, внешний PostgreSQL с CA, broker/cache, выбранное хранилище, Ingress TLS и Keycloak.
3. Создайте Secrets через корпоративное хранилище по [руководству установки](docs/04_DEPLOYMENT_GUIDE.md). Передайте только имена объектов и ключей. Для локальной репетиции используйте выделенный путь ниже.
4. Выполните preflight, установку и smoke по руководству. Проверьте Keycloak на тестовых аккаунтах и завершите [единый чеклист](checklists/DEPLOYMENT_CHECKLIST.md).
5. При сбое сохраните состояние Helm и Kubernetes events и откройте [runbook](docs/16_TROUBLESHOOTING.md). Для решений о запуске используйте release gates.

На другой машине соберите из проверенного SHA Django и nginx. Скрипт публикации проверяет digest обоих образов и записывает их в Helm values. [Инструкция по сборке и публикации](docs/18_BUILD_AND_IMAGE_TRANSFER.md).

## Отдельная лаборатория на одном узле OrbStack

В каталоге Enterprise Delivery Package или `deploy/handover` используйте Helm, kubectl, Python 3.11+ с PyYAML и четыре доступных узлу образа. В примере Django и nginx обозначены переменными с полными ссылками на образы, собранные из application SHA. PostgreSQL 18.6 и Valkey 9.1.2 получаются из утверждённого registry. Команда создаёт новый namespace и отдельные зависимости. Для другого локального порта укажите `ASPM_LAB_PORT` перед подготовкой namespace и используйте тот же порт в port-forward и `--url`. Профиль использует HTTP на loopback, RWO и отдельную PostgreSQL.

Для checkout из Git задайте `ASPM_CHART_ARGS=(--chart ../helm/aspm)`. Для распакованного архива задайте `ASPM_CHART_ARGS=()`, чтобы использовать чарт из манифеста.

```bash
scripts/prepare-lab.sh orbstack aspm-lab-handover local-path \
  postgres:18.6-alpine valkey/valkey:9.1.2 \
  "${ASPM_DJANGO_IMAGE:?укажите ссылку на Django image}" \
  "${ASPM_NGINX_IMAGE:?укажите ссылку на nginx image}"
scripts/deploy.sh --context orbstack --namespace aspm-lab-handover --release aspm \
  --profile local --arch arm64 "${ASPM_CHART_ARGS[@]}" \
  -f values-aspm-lab-handover.yaml --apply
kubectl --context orbstack -n aspm-lab-handover port-forward \
  --address 127.0.0.1 service/aspm-aspm 18739:80
```

В отдельном терминале повторите проверки опубликованного URL.

```bash
scripts/smoke-test.sh --context orbstack --namespace aspm-lab-handover --release aspm \
  --profile local --arch arm64 --url http://127.0.0.1:18739
```

Откройте `http://127.0.0.1:18739/login`. Для первоначального лабораторного доступа создайте тестового SecOps интерактивно через `kubectl --context orbstack -n aspm-lab-handover exec -it deployment/aspm-aspm-web -c web -- python manage.py createsuperuser`. Для корпоративного входа настройте [Keycloak](docs/06_KEYCLOAK_AD_SETUP.md).

## Мониторинг

[Helm overlays, VictoriaMetrics и Grafana JSON](monitoring/README.md).
