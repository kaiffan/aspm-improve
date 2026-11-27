# 18 | Сборка, публикация и установка на другой машине

Этот путь собирает два образа ASPM 1.0.1 с мониторингом. Kubernetes использует Django image для web, workers, Beat, миграций и metrics sidecars. Второй образ запускает nginx. Для сборки нужны Bash, Python 3.10+, Git, tar, Docker с Buildx, свободное место и доступ к базовым образам, PyPI, APT/APK и Yarn. Выберите архитектуру Kubernetes-узлов. На ARM64 используйте linux/arm64, на AMD64 используйте linux/amd64. Для корпоративной поставки собирайте на runner нужной архитектуры.

## 1. Перенести комплект

Скопируйте на другую машину архив ASPM-1.0.1-Enterprise-Delivery.tar.gz и соседний файл .sha256. В каталоге с обоими файлами выполните:

```bash
shasum -a 256 -c ASPM-1.0.1-Enterprise-Delivery.tar.gz.sha256
tar -xzf ASPM-1.0.1-Enterprise-Delivery.tar.gz
cd ASPM-1.0.1-Enterprise-Delivery
shasum -a 256 -c SHA256SUMS
```

На Linux с GNU coreutils вместо shasum -a 256 используйте sha256sum. Хеш архива сверяйте с контрольной суммой, полученной по доверенному каналу.

## 2. Собрать и отправить образы

Укажите hostname и project вашего registry. В Harbor заранее создайте проект и выдайте build runner право push. Kubernetes достаточно отдельного доступа pull.

```bash
ASPM_ARCH=amd64
ASPM_REGISTRY=registry.example.com
ASPM_IMAGE_PREFIX="$ASPM_REGISTRY/platform/aspm"
ASPM_BUILD_DIR="$PWD/aspm-build"

SOURCE_DIR=$(python3 scripts/prepare-monitoring-source.py "$ASPM_BUILD_DIR")
scripts/build-images.sh --monitoring "linux/$ASPM_ARCH" "$ASPM_IMAGE_PREFIX" "$SOURCE_DIR"

docker login "$ASPM_REGISTRY"
scripts/publish-images.sh "linux/$ASPM_ARCH" "$ASPM_IMAGE_PREFIX" images.registry.yaml
```

Подготовка проверяет SHA-256 исходного архива и патча, применяет патч в чистом каталоге и записывает ревизию мониторинга. Повторную сборку можно выполнить в уже подготовленном SOURCE_DIR, а новую распаковку запускайте с новым ASPM_BUILD_DIR. Для CI передавайте registry token в docker login --password-stdin из хранилища секретов.

Скрипт публикации проверяет platform и source label обоих образов до push, затем забирает каждый образ по digest и сравнивает image ID. Файл images.registry.yaml содержит два repository@sha256 и DD_ASPM_GIT_SHA в форме Helm values. Сохраните его рядом с release evidence. Сборка и публикация ограничены одной архитектурой за запуск. Выпускайте образ и overlay отдельно для каждой архитектуры. Исторический [паспорт образов](../provenance/IMAGES.json) относится к исходному кандидату, а новые digests создаёт ваш registry. После сборки выполняйте сканирование и SBOM с той же парой образов.

## 3. Развернуть

Подготовьте Kubernetes 1.27+, context и namespace. Установите PyYAML, kubectl и Helm с поддержкой dry-run=server. Для production-профиля заполните [site values и зависимости](04_DEPLOYMENT_GUIDE.md). В namespace должен существовать Secret для pull из private registry. Если узлам нужен частный CA registry, доверьте его в container runtime узлов. Такой CA отличается от CA для remote_write в VictoriaMetrics.

Добавьте в site.yaml имя существующего pull secret, если registry закрыт.

```yaml
imagePullSecrets:
  - name: aspm-registry-pull
```

Скопируйте [overlay существующего Prometheus](../monitoring/helm-values/values-monitoring-existing.example.yaml) в monitoring.site.yaml и заполните selectors, если сбор выполняет корпоративный Prometheus Operator. Его администратор настраивает [отдельное назначение VictoriaMetrics](../monitoring/prometheus/remote-write.operator.example.yaml). Для отдельного Prometheus используйте [dedicated overlay](../monitoring/helm-values/values-monitoring-dedicated.example.yaml) и [remote write overlay](../monitoring/helm-values/values-victoriametrics-remote-write.example.yaml) с вашим URL и Secret. Включайте один collector для релиза.

```bash
ASPM_CONTEXT=my-staging
ASPM_NAMESPACE=aspm

scripts/deploy.sh --context "$ASPM_CONTEXT" --namespace "$ASPM_NAMESPACE" \
  --release aspm --profile ha --arch "$ASPM_ARCH" \
  -f site.yaml -f images.registry.yaml -f monitoring.site.yaml --apply
```

Команда сама выполняет preflight, deploy и smoke. Для preflight без установки используйте scripts/preflight.sh с теми же параметрами и без --apply. Чарт выбирается по манифесту поставки и сверяется с его SHA-256. Helm overlays передаются в показанном порядке, чтобы images.registry.yaml перекрыл примеры registry из site.yaml. В корпоративной Grafana импортируйте [готовые JSON](../monitoring/provisioning/README.md).
