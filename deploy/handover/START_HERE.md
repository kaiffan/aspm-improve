# ASPM 1.0.1 | Начало работы

ASPM объединяет классическое управление уязвимостями DefectDojo и приём результатов CI/CD с привязкой к репозиторию и коммиту. Версия приложения 1.0.1, Helm 0.1.0-rc.9. Статусы и идентификаторы кандидата указаны в [паспорте](DELIVERY_MANIFEST.json) и [решении о выпуске](qualification/RELEASE_GATE.md).

1. Распакуйте архив в новый каталог. В корне пакета выполните `shasum -a 256 -c SHA256SUMS` или `sha256sum -c SHA256SUMS`. Каждая строка должна содержать `OK`.
2. Заполните [анкету инфраструктуры](checklists/INFRASTRUCTURE_INPUT.md). Для корпоративного staging используйте Standard HA и подготовьте согласованные registry, namespace, внешний PostgreSQL с CA, broker/cache, два RWX PVC, Ingress TLS и Keycloak.
3. Создайте Secrets через корпоративное хранилище по [руководству установки](docs/04_DEPLOYMENT_GUIDE.md). Передайте только имена объектов и ключей. Для локальной репетиции используйте выделенный путь ниже.
4. Выполните preflight, установку и smoke по руководству. Проверьте Keycloak на тестовых аккаунтах и завершите [единый чеклист](checklists/DEPLOYMENT_CHECKLIST.md).
5. При сбое сохраните состояние Helm и Kubernetes events и откройте [runbook](docs/16_TROUBLESHOOTING.md). Для решений о запуске используйте release gates.

## Отдельная лаборатория на одном узле OrbStack

Нужны Helm, kubectl, Python 3.10+ с PyYAML и четыре доступных узлу образа. Загрузите два образа ASPM из отдельного ARM64 архива или соберите их из исходников. PostgreSQL 18.6 и Valkey 9.1.2 получаются из утверждённого registry. При необходимости замените их ссылки на доступные узлу копии. Получите точные теги из паспорта образов. Следующая команда создаёт новый namespace и отдельные зависимости. Выберите новый namespace. Для другого локального порта укажите ASPM_LAB_PORT до prepare-lab и используйте его в port-forward и --url. Профиль использует HTTP на loopback, RWO и тестовую PostgreSQL.

```bash
scripts/prepare-lab.sh orbstack aspm-lab-handover local-path \
  postgres:18.6-alpine valkey/valkey:9.1.2 \
  aspm-qualified/django:bef347c845ee-arm64 aspm-qualified/nginx:bef347c845ee-arm64
scripts/deploy.sh --context orbstack --namespace aspm-lab-handover --release aspm \
  --profile local --arch arm64 -f values-aspm-lab-handover.yaml --apply
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
