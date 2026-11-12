# RC2: воспроизведение на сохранённом локальном стенде

Runtime source: `25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb`. Release/QA HEAD может быть новее; runtime diff должен отсутствовать. Все команды выполняются в worktree `release/1.0.1-rc2`, не в пользовательской feature-ветке. Не смешивать старый API8080 с оптимизированной сборкой48091.

## Конфигурация и данные

Нужны существующие Docker images из `build.json`, основная PostgreSQL18.6, неизменный `dd_round4_seed` с1 000 168 findings, существующая `aspm_rc2_validation` и отдельный `dd-final-tests` PostgreSQL volume. Скрипты не удаляют/пересоздают БД и не запускают migrations. Никаких `down -v`/DROP/VACUUM FULL.

`scripts/common.py` вычисляет repo root и private path относительно worktree. Private каталог — соседний `aspm-rc2-private`, mode0700; env/credentials/inspect JSON —0600, вне Git. Подготовка разрешённых auth sessions пишет только django_session на seed/copy; findings/products/memberships не изменяются. Основная source читается только для integrity fingerprints. Во время нагрузки не запускать worker/beat над seed, full tests, browser audit, сборки или другие benchmark stacks.

После исчезновения `/private/tmp` retained containers сохраняли environment/mount/volume metadata. Для данного стенда `containers.json` приватно получен через `docker inspect` контейнеров, перечисленных в `prepare.py`/`test_suite.py`; не печатать этот JSON. Публичная release Compose/env template остаётся в `release/1.0.1`, секреты заполняются локально. Для другого стенда потребуются его private connection/volume names; автоматически брать чужую БД запрещено.

Существующие raw-файлы одной серии не перезаписывать. Для нового опыта сначала перенести весь evidence cohort в отдельный timestamp archive и сохранить причину/параметры, либо использовать отдельный чистый QA worktree. Не складывать новые повторы с этим cohort автоматически. Write-smoke создаёт ограниченный набор fixtures только на validation; для нового независимого write-опыта использовать отдельную контролируемую копию или сохранённый успешный write context.

## Последовательность

1. Проверить branch/SHA/diff, AC power, low power=0, Docker limits; исходный checkout не менять.
2. Сохранить runtime configuration приватно и запустить **только существующий** main PostgreSQL. `python3 release/1.0.1/rc2/scripts/prepare.py` сверяет seed/source fingerprints, восстанавливает изолированный gateway и25 существующих identities.
3. Воспроизводимая сборка из точного SHA, pinned base digests и GNU msgfmt:

```sh
python3 release/1.0.1/scripts/build_images.py \
  --sha 25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb \
  --context /private/path/empty-build-context \
  --manifest release/1.0.1/rc2/build-reproduced.json
python3 release/1.0.1/rc2/scripts/provenance.py
```

`provenance.py` дополнительно читает `build-reproduced.json` и сверяет2233 app/40 static files, image IDs и все dependency versions. При новом build context выполнить именно эти проверки, не только labels.

4. `python3 release/1.0.1/rc2/scripts/test_suite.py` — штатный wrapper, полный `unittests`, только offline test PostgreSQL. Ожидаемые текущие blockers не отключаются; wrapper exit и все errors/skips записаны. `baseline_tests.py` отдельно показывает те же2 errors на R5/RC1 и red/green pagination/grade-cache. После тестов stack останавливается без удаления volumes.
5. `caffeinate -dimsu python3 release/1.0.1/rc2/scripts/campaign.py` — три сборки по очереди на одном порту/seed.45 mixed +60 endpoint runs, fixed workload/seeds/actors; контроль OOM,5xx, AC/lowpower, Docker memory7.2GiB, host free12%, swap growth. Resource stop нельзя удалять для сокрытия ошибки. Подготовительный manual stop сохранён в `excluded/preflight-paused`.
6. `npm ci --ignore-scripts --no-audit --no-fund` и `npx playwright install chromium` в `release/1.0.1/browser`; зависимости зафиксированы package-lock. Это QA dependencies, не runtime application requirements.
7. `python3 release/1.0.1/rc2/scripts/finalize.py` — после campaign: RC1 red / RC2 green browser checks,50-page audit, expanded filters, server pagination matrix, bounded real ZAP import/reimport/duplicates, actual CSRF form/login, две vulnerability references,18 complete JSON rollback pairs. Сначала переключение на validation, собственный broker/cache, worker1, без beat. Credentials/output paths задаёт helper; никакого HAR/trace с cookies.
8. `python3 release/1.0.1/rc2/scripts/verify.py`, затем `analyze.py`, `plot.py`, `report.py`. Для графиков: `UV_CACHE_DIR=/private/path/cache uv run --no-project --with matplotlib==3.10.7 python release/1.0.1/rc2/scripts/plot.py`. Node: `node --test release/1.0.1/scripts/theme.test.cjs`. Ruff0.16.10 — configruff.toml на изменённых runtime/test files.

Raw observations, CPU/RSS/buffer/temp windows и per-run images/SHA сохраняются до агрегации. p50 median, остальные percentile nearest rank; p99 только n≥300; pooled p95 не среднее p95. RPS=ΣN/Σelapsed. Report generation не преобразует errors в skips и не добавляет несуществующие metrics. PG CPU100%=ядро; RSS shared memory может считаться несколько раз.

Финальный demo использует source25fb63ae, validation DB, локальные candidate images и собственный broker/cache. Измерительный middleware удалён. Stable/RC2 alias не promoted: full-suite blockers ещё требуют разрешения.

В этой серии первый collector ошибочно выводил первичную сортировку из queryset после prefetch. Попытка сохранена в diagnostics/prefetch-order-metadata; recapture_profiles.py исправил только диагностические профили, не105 нагрузочных raw-файлов. Текущий collector использует исходный FilterSet до pagination/prefetch и ожидает403 для закрытых users/notes. Дополнительные rapid.cjs и Node red guard результаты записаны отдельно.
