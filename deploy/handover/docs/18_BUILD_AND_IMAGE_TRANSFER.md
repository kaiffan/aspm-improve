# 18 | Сборка и перенос образов

Паспорт [IMAGES.json](../provenance/IMAGES.json) хранит точный source SHA, локальные OCI index/config ID и ссылки на CycloneDX. Worker, Beat и migration используют Django image. Registry digests заполняются после публикации в согласованный внутренний registry и проверки manifest архитектуры.

## Лаборатория Linux/ARM64

Для отдельного файла ASPM-1.0.1-linux-arm64-images.tar.gz выполните проверку SHA-256 из его sidecar и импорт. Образы PostgreSQL/Valkey подключаются отдельно. Для OrbStack Docker context должен использовать тот же image store, что и лабораторный узел.

```bash
shasum -a 256 -c ASPM-1.0.1-linux-arm64-images.tar.gz.sha256
docker load --input ASPM-1.0.1-linux-arm64-images.tar.gz
docker image inspect aspm-qualified/django:bef347c845ee-arm64 --format '{{.Os}}/{{.Architecture}} {{.Id}}'
docker image inspect aspm-qualified/nginx:bef347c845ee-arm64 --format '{{.Os}}/{{.Architecture}} {{.Id}}'
```

## Сборка из архива

Сверьте SHA256SUMS и распакуйте исходный архив в отдельную директорию. На машине утверждённой архитектуры запустите build script из корня поставки. Нужны Docker BuildKit, доступ к pinned base digests, PyPI, APT/APK и Yarn, а также approved registry prefix или локальный prefix.

```bash
tar -xzf source/aspm-1.0.1-source.tar.gz -C "$ASPM_BUILD_DIR"
scripts/build-images.sh linux/amd64 aspm-build "$ASPM_BUILD_DIR/aspm-1.0.1-source"
```

Для ARM64 замените платформу на linux/arm64. Скрипт собирает два release target, записывает OCI source labels, проверяет platform и показывает локальные IDs. Нативную AMD64 сборку выполняйте на согласованном runner. После сборки сверяйте зависимости, запускайте SBOM, vulnerability scan и deployment smoke с той же парой образов. APT/APK и разрешение транзитивных библиотек могут изменяться со временем. Для передачи точных ARM64 образов используйте архив с проверенными IDs.

Исходный срез позволяет повторить build из указанного коммита. Исторические отчёты и перечисленные в source/EXCLUDED_FIXTURES.txt тестовые fixtures с секретоподобными строками или путями локального компьютера убраны. Для полного upstream test suite используйте разрешённый checkout этого SHA с fixtures.

Для release engineering есть scripts/assemble-delivery.py. Он принимает checkout, испытанный chart .tgz, каталог qualification inputs и evidence SHA, проверяет содержимое Chart, относительные ссылки, безопасные пути tar и SHA-256. В рабочем каталоге assembly должны быть rc-source из application SHA, Trivy результаты и SBOM, images.json, готовый PDF и очищенные evidence. Raw credentials, state и base dumps остаются вне staging доставки.
