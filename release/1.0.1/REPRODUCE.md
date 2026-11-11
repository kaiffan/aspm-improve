# Повторение release-проверок

## Источники и безопасность

Application source — SHA из `measurements/build-rc.json`; baseline Round5 — `c6a6144ed93b83adb1fd4ea9daa2c5e417ecea37`; Original — чистый официальный3.5.100 `334bef02d65a74909fe976b22724526474d5a0f6`. История не объединялась со случайным current origin/dev или веткой кастомных Engagements. Публичные source/image IDs: build manifests, git_baseline.json и inherited R5 source_verification.json.

Собрать RC по BUILD.md. Для Original/R5 использовать те же dependency images из build-lock.json и существующие `perf-report/final/build_images.py` / `perf-report/round5/build_image.py`, указав точный SHA и пустой context. Имена сравниваемых образов в benchmark_release.py; сверить реальные IDs перед прогоном. Ни одна сборка не запускает миграции.

Нужны существующие PostgreSQL/Valkey, отдельная контрольная копия БД и private Compose/env/accounts вне Git. Не использовать рабочую БД с test runner. Не выполнять `down -v`, DROP, VACUUM FULL или неконтролируемый импорт. Исходная БД и seed сохраняются.

В текущем стенде: source содержит1 000 168 findings; `dd_round4_seed` — неизменный baseline для read-only HTTP, `aspm_rc1_validation` — write/browser/import-копия. Сравнивать fingerprints до/после. После writes validation имеет1 000 293 rows и не должна подменять миллионную базу для честного A/B. Все исходные строки validation также сверяются по prefix/hash.

## Нагрузка

Private Compose проекта `aspm-rc1`: app service `aspm`, nginx48086, одинаковые4×4 uWSGI и PG/Docker limits; только эти app/nginx переключаются по одному. Нет initializer/beat/worker над baseline. Общая версия schema проверена management checks и отсутствием migrations. Перед запуском остановить старые benchmark-sidecars, записать и потом восстановить их состояния.

Для SQL count/time временно подключить одинаковый `perf-report/round5/perf_instrument.py` как middleware через private extra_settings. Cache namespace различать между вариантами/БД. Не публиковать SQL bindings, credentials, headers, HAR или trace. После тестов убрать инструментирование из demo.

Accounts JSON —25 объектов: token/session/product/finding/test/engagement плюс поля, требуемые `perf-report/round5/scenarios.json`; secrets только в private файле0600. Использовать существующие scoped accounts; не создавать25 superusers.

```sh
caffeinate -dimsu python3 release/1.0.1/scripts/benchmark_release.py \
  --compose /private/path/compose.json --credentials /private/path/accounts.json \
  --phase endpoints --variants round5,ui --repeats 2 --requests 60 \
  --stop-file /private/path/new-stop

caffeinate -dimsu python3 release/1.0.1/scripts/benchmark_release.py \
  --compose /private/path/compose.json --credentials /private/path/accounts.json \
  --phase mixed --variants round5,ui --levels 1,5,10,15,25 \
  --repeats 2 --requests 300 --stop-file /private/path/new-stop

# Point the private runtime to the protected million-row baseline first.
# Stop every worker consuming that environment's broker before this comparison.
caffeinate -dimsu python3 release/1.0.1/scripts/benchmark_release.py \
  --compose /private/path/compose.json --credentials /private/path/accounts.json \
  --phase mixed --variants original,round5,rc --levels 25 --label-prefix final \
  --repeats 2 --requests 300 --stop-file /private/path/new-stop
```

Варианты `ui`/`rc` ссылаются на source/images из сохранённых manifests. UI — промежуточная замороженная сборка, rc — финальный код. При новом выпуске обновлять manifest осознанно, не переименовывать старые raw результаты.

Warmup5 для endpoint и25 для mixed; seeds35101/35102; request timeout90s/deadline360s. Mixture неизменна, см. PERFORMANCE.md. Stop-file означает реальную остановку: исследовать причину, архивировать окно, не удалять для сокрытия ошибки. Guard контролирует power, OOM, memory/swap, monitor failures; временный caffeinate не меняет постоянные power settings. PG DB scope определяется из реально запущенного app.

Profile выполняется отдельно: `--phase profile --variants round5,rc --repeats 1`. Полные JSON hashes и HTML/context/table values сохраняются; cached Simple Metrics может не посылать template-render signal, поэтому дополнительно сравниваются все numeric cells, а cold semantic context — полностью.

```sh
python3 release/1.0.1/scripts/compare_profiles.py --after rc --output compatibility-final.json
python3 release/1.0.1/scripts/analyze.py
# matplotlib venv: inherited perf-report/final/chart-requirements.txt
MPLCONFIGDIR=/private/path/mpl /path/to/venv/bin/python \
  release/1.0.1/scripts/plot_results.py
```

Финальная тройка, ранние saturation и follow-up phase не усредняются между собой. RPS =Σrequests/Σelapsed; p95/p99 из объединённых observations данной конфигурации, не среднее p95. Сохранять run-level values и реальные ошибки. p99 только приn≥300; per-case p95 приn≥20.

## Автотесты и браузер

`tests.compose.json` private: отдельный тестовый PostgreSQL/Valkey, test-image по `perf-report/final/Dockerfile.tests` с APP_IMAGE точного RC. Поднять stack перед wrapper; потом остановить без удаления volumes. Модули перечислены в tests-final.log/TEST_RESULTS.md. Не запускать pytest/manage.py test над миллионной БД.

```sh
node --test release/1.0.1/scripts/theme.test.cjs
COMPOSE_FILE=/private/path/tests.compose.json COMPOSE_PROJECT_NAME=dd-final-tests \
  ./run-unittest.sh --test-case 'unittests.test_aspm_release_ui unittests.test_product_announcements unittests.test_round5_performance'
```

Browser dev setup: npm ci в release/1.0.1/browser, pinned Playwright/axe; установить Chromium. Credentials через ASPM_CREDENTIALS, browser cache через PLAYWRIGHT_BROWSERS_PATH. После readiness запускать validate.cjs, interactions.cjs; performance.cjs отдельно от других нагрузок (32 descriptive navigations). Baseline gateway48089 должен иметь frozen R5 static и тот же gzip, а не API-only gateway48085.

## Writes / import / rollback

Только validation-копия и её отдельные broker/cache namespaces. Для реального ZAP цикла `import_smoke.py` читает private credentials со stdin; rounds1,40 alerts×3URL, reimport4..43 и duplicate peer. Перед ним запустить worker того же image, prefork1/prefetch1; не запускать beat. Временно enable_deduplication только на копии, обязательно fresh System_Settings.objects.get(no_cache=True), сохранить/восстановить флаг, mail locmem. Не обновлять cached read-only instance и не менять dedup-код. Проверить состояние очереди перед тестом; не удалять уже поставленные задачи.

Create/edit через write_checks.cjs использует реальную Django form/CSRF; CodeMirror API синхронизирует backing textarea. Можно продолжить уже созданный fixture через private write context, чтобы не плодить строки. Upstream title capitalization сохраняется. Access-free user создаётся seed_login_check.py только при явном NAME=aspm_rc1_validation; password/token остаются private. Проверить foreign finding API/filter/FAST и отсутствие данных в UI denial.

`rollback_check.py` переключает R5→RC на одной validation-копии и сравнивает18 полных JSON пар. Предварительно остановить worker, дождаться очереди; после восстановить только RC worker. После всех gates вернуть private runtime на validation, удалить perf middleware/binds и оставить нормальный demo48086. Источник/seed всегда сверить заново. Production rollout/rollback не был выполнен; инструкции DEPLOY/ROLLBACK.
