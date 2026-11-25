# Воспроизведение

## Native Linux AMD64

Checkout должен содержать A, B и каталог отчёта. На Linux VM откройте shell в корне репозитория. Нужен свободный loopback порт 48115. Для Debian/Ubuntu Playwright устанавливает системные зависимости командой install-deps, если они ещё не установлены.

```sh
repo="$PWD"
kit="$repo/integration-report/zero-finalize-final-qualification/native"
mkdir -p "$repo/.cache"
state="$repo/.cache/zfq-native"
cd "$repo/release/1.0.1/browser"
npm ci
npx playwright install chromium
export NODE_PATH="$PWD/node_modules"
cd "$repo"
python3 "$kit/build.py" --repo "$repo" --state "$state" --plan
python3 "$kit/campaign.py" --state "$state" plan
python3 "$kit/build.py" --repo "$repo" --state "$state"
python3 "$kit/campaign.py" --state "$state" init
python3 "$kit/campaign.py" --state "$state" seed
python3 "$kit/campaign.py" --state "$state" core9
python3 "$kit/campaign.py" --state "$state" acceptance
python3 "$kit/summarize.py" --state "$state" > "$state/raw/ab-summary.json"
python3 "$kit/campaign.py" --state "$state" load --fixtures "$repo/unittests/scans" --rows 1500
python3 "$kit/campaign.py" --state "$state" stop
```

Перед нагрузкой проверить raw/host.json, raw/io-preflight.json и raw/snapshot-restore.json. При guard или business failure сохраняются рабочая БД и уже записанные samples. Перед повтором требуется разобрать причину. Сухой план, Compose config и входные SHA-256 проверены на Mac. Фактический Linux run остаётся отдельной проверкой.

Результаты находятся в state/raw. Каталог state также содержит private owner/account files и dump. Переносите только проверенное содержимое raw. Native load использует свою БД и сохраняет метрики отдельно от Core9 и Acceptance.

## Локальные измерения

scripts/overview.py запускается в manage.py shell на собственной небольшой PostgreSQL базе с QUAL_VARIANT=A, B0 или B1. Fixtures откатываются. scripts/local_load_metrics.py и scripts/faults_local.py предназначены для локального проекта zfq-load с проверкой ownership label. Для другой установки используйте portable campaign.py load, который создаёт изолированную лабораторную БД.

```sh
ASPM_TEST_API_ONLY=True ./run-unittest.sh --test-case 'unittests.test_aspm_zero_finalize unittests.test_aspm_ingestion unittests.test_aspm_integration unittests.test_finding_write_concurrency unittests.test_deduplication_logic unittests.test_importers_deduplication unittests.test_utils_deduplication_reopen unittests.test_product_stats unittests.test_product_metrics_aggregation unittests.test_product_metrics_closed_count'
```

[Описание Ryzen](RYZEN_DEPLOYMENT.md) · [Входы и SHA-256](native/workload-lock.json)
