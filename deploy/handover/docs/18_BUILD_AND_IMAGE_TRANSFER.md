# 18 | Сборка, публикация и установка на другой машине

Этот путь собирает два образа ASPM 1.0.1 с мониторингом. Kubernetes использует Django image для web, workers, Beat, миграций и metrics sidecars. Второй образ запускает nginx. Для сборки нужны Bash, Python 3.11+, Git, tar, Docker с Buildx, свободное место и доступ к базовым образам, PyPI, APT/APK и Yarn. Выберите архитектуру Kubernetes-узлов. На ARM64 используйте linux/arm64, на AMD64 используйте linux/amd64. Для корпоративной поставки собирайте на runner нужной архитектуры.

## 1. Получить исходники

Для доставки из Git подставьте в `ASPM_RELEASE_REF` и `ASPM_EXPECTED_SHA` опубликованную ветку и согласованный SHA итогового дерева. Установите Bash, Git, tar, Python 3.11+ с PyYAML, Docker с Buildx, Helm и kubectl.

```bash
git clone https://github.com/kaiffan/aspm-improve.git
cd aspm-improve
git switch "$ASPM_RELEASE_REF"
test "$(git rev-parse HEAD)" = "$ASPM_EXPECTED_SHA"
cd deploy/handover

ASPM_APP_SHA=$(python3 -c 'import json; print(json.load(open("DELIVERY_MANIFEST.json"))["application_sha"])')
git merge-base --is-ancestor "$ASPM_APP_SHA" HEAD
SOURCE_DIR=$(mktemp -d)
git archive "$ASPM_APP_SHA" | tar -xf - -C "$SOURCE_DIR"
printf '%s\n' "$ASPM_APP_SHA" > "$SOURCE_DIR/.aspm-source-revision"
ASPM_CHART_ARGS=(--chart ../helm/aspm)
```

Для доставки архивом скопируйте ASPM-1.0.1-Enterprise-Delivery.tar.gz и соседний файл .sha256. В каталоге с обоими файлами выполните следующие команды.

```bash
shasum -a 256 -c ASPM-1.0.1-Enterprise-Delivery.tar.gz.sha256
tar -xzf ASPM-1.0.1-Enterprise-Delivery.tar.gz
cd ASPM-1.0.1-Enterprise-Delivery
shasum -a 256 -c SHA256SUMS
ASPM_CHART_ARGS=()
ASPM_BUILD_DIR=$(mktemp -d)
tar -xzf source/aspm-1.0.1-source.tar.gz -C "$ASPM_BUILD_DIR"
SOURCE_DIR="$ASPM_BUILD_DIR/aspm-1.0.1-source"
```

На Linux с GNU coreutils вместо shasum -a 256 используйте sha256sum. Хеш архива сверяйте с контрольной суммой, полученной по доверенному каналу.

## 2. Собрать и отправить образы

Укажите hostname и project вашего registry. В Harbor заранее создайте проект и выдайте build runner право push. Kubernetes достаточно отдельного доступа pull.

```bash
ASPM_ARCH=amd64
ASPM_REGISTRY=registry.example.com
ASPM_IMAGE_PREFIX="$ASPM_REGISTRY/platform/aspm"
scripts/build-images.sh "linux/$ASPM_ARCH" "$ASPM_IMAGE_PREFIX" "$SOURCE_DIR"

docker login "$ASPM_REGISTRY"
scripts/publish-images.sh "linux/$ASPM_ARCH" "$ASPM_IMAGE_PREFIX" images.registry.yaml
```

Исходники rc.11 включают мониторинг и S3. Скрипты сборки и публикации по умолчанию используют `application_sha` из манифеста. Для прежнего комплекта с отдельной ревизией мониторинга передайте `--monitoring` обоим скриптам. Для CI передавайте registry token в `docker login --password-stdin` из хранилища секретов.

Скрипт публикации проверяет platform и source label обоих образов до push, затем забирает каждый образ по digest и сравнивает image ID. Файл images.registry.yaml содержит два repository@sha256 и DD_ASPM_GIT_SHA в форме Helm values. Сохраните его рядом с release evidence. Сборка и публикация ограничены одной архитектурой за запуск. Выпускайте образ и overlay отдельно для каждой архитектуры. Исторический [паспорт образов](../provenance/IMAGES.json) относится к исходному кандидату, а новые digests создаёт ваш registry. После сборки выполняйте сканирование и SBOM с той же парой образов.

## 3. Развернуть

Подготовьте Kubernetes 1.27+, context и namespace. Установите PyYAML, kubectl и Helm с поддержкой dry-run=server. Для production-профиля заполните [site values и зависимости](04_DEPLOYMENT_GUIDE.md). В namespace должен существовать Secret для pull из private registry. Если узлам нужен частный CA registry, доверьте его в container runtime узлов. Такой CA отличается от CA для remote_write в VictoriaMetrics.

Добавьте в site.yaml имя существующего pull secret, если registry закрыт.

```yaml
imagePullSecrets:
  - name: aspm-registry-pull
```

Для объектного профиля подготовьте storage.site.yaml по [примеру S3](../config/values-storage-s3.example.yaml) и [руководству](19_S3_STORAGE_AND_CUTOVER.md). Для файлового профиля используйте соответствующий filesystem или RWX overlay.

Скопируйте [overlay существующего Prometheus](../monitoring/helm-values/values-monitoring-existing.example.yaml) в monitoring.site.yaml и заполните selectors, если сбор выполняет корпоративный Prometheus Operator. Его администратор настраивает [отдельное назначение VictoriaMetrics](../monitoring/prometheus/remote-write.operator.example.yaml). Для отдельного Prometheus используйте [dedicated overlay](../monitoring/helm-values/values-monitoring-dedicated.example.yaml) и [remote write overlay](../monitoring/helm-values/values-victoriametrics-remote-write.example.yaml) с вашим URL и Secret. Включайте один collector для релиза.

```bash
ASPM_CONTEXT=my-staging
ASPM_NAMESPACE=aspm

scripts/deploy.sh --context "$ASPM_CONTEXT" --namespace "$ASPM_NAMESPACE" \
  --release aspm --profile ha --arch "$ASPM_ARCH" "${ASPM_CHART_ARGS[@]}" \
  -f site.yaml -f images.registry.yaml -f monitoring.site.yaml -f storage.site.yaml --apply
```

Команда выполняет preflight, deploy и smoke. Для отдельного preflight запустите `scripts/preflight.sh` с теми же параметрами без `--apply`. Из checkout используется чарт в `deploy/helm/aspm`. Для архива скрипт сверяет SHA-256 чарта с манифестом. Сохраните показанный порядок overlays, чтобы `images.registry.yaml` перекрыл ссылки на образы из `site.yaml`. В Grafana импортируйте [поставляемые JSON](../monitoring/provisioning/README.md).
