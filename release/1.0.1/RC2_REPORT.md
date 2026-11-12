# ASPM 1.0.1 RC2 — release hardening

**Кандидат подготовлен, формальный выпуск заблокирован двумя унаследованными test import errors.** Все runtime исправления в отдельных commits на `release/1.0.1-rc2`; frozen image source `25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb`. Данные основной БД **1 000 168 findings** и protected seed сохранены по count/sum/full-row fingerprints. Изолированная write-copy теперь содержит 1,000,508 findings; исходный prefix также неизменен.

## Подтверждённые дефекты и минимальные исправления

| Дефект | Исправление | Evidence |
|---|---|---|
| Clear сбрасывал только controls, URL/results оставались отфильтрованы | Native reset navigation для #clear; #clear_js оставлен in-place | Real RC1 red / RC2 green |
| Nonunique UI order давал overlap, malformed page_size —500; огромный size был неограничен | Lazy model QuerySet получает PK после прежних sort keys; bad size→default, cap=max(250,server default) | 9 unit tests + live matrix |
| Finding paginator обращался к .query у list в delete-preview | DRF fallback для non-QuerySet | 2 regression tests + full suite |
| Expanded filters содержали unnamed Select2 controls, поздняя init обходила load handler | Существующие labels на combobox/search; field-local observers | 3 Node regressions + desktop/mobile axe |
| Full-suite grade query tests зависели от cache marker соседней fixture | Test-only setup/cleanup нужного key | 45-case red/green; query expectations unchanged |

Валидные Product ID/name+severity+active запросы и permissions работали до исправления reset; серверный Product filter не переписывался. Стандартный REST формат, сортировка и точные count не изменены. Глобальный FAST, новые migrations/indexes или application services не добавлялись; отдельный test broker/cache восстановлен для изоляции стенда, нового глобального cache нет. OTP branding/themes/redesign сохранены. Дополнительные изменения — metadata и portable offline Jira DNS test, не новые функции.

## Сопоставимые результаты

| Показатель, c25 | Round 5 | RC1 | RC2 |
|---|---:|---:|---:|
| Mixed p50, s | 0.751 | 0.726 | 0.744 |
| Mixed p90, s | 1.788 | 1.695 | 1.764 |
| Mixed p95, s | 5.480 | 5.505 | 5.485 |
| Mixed p99, s | 10.455 | 10.285 | 10.699 |
| Mixed RPS | 16.845 | 17.414 | 17.161 |
| PostgreSQL CPU, % (100%=ядро) | 533.008 | 549.302 | 527.574 |
| uWSGI CPU, % | 115.285 | 103.268 | 102.235 |
| App container peak, MiB | 980.700 | 943.000 | 963.200 |
| Один worker peak RSS, MiB | 313.410 | 321.648 | 345.340 |
| Среднее SQL execute/request, ms | 741.010 | 721.196 | 728.958 |
| HTTP errors | 0 | 0 | 0 |
| Наблюдения / повторы | 900 / 3 | 900 / 3 | 900 / 3 |

RC2 относительно Round 5: p95 +0.08%, RPS +1.88%. Это описательное сравнение трёх повторов, а не доказательство статистической значимости. Оба отклонения укладываются в ориентир ±10%; доказанной существенной регрессии в этой серии не установлено. Ускорение RC2 не заявляется.

Новая серия: 17,100 HTTP requests, 45 pooled scenarios, 105 runs; c25 по3 repeats/build. Исторические серии не подмешаны. HTTP errors в проверенной серии: 0. [Методика/таблицы/графики](RC2_PERFORMANCE.md), [raw JSON](rc2/benchmark_results.json).

## Проверки и статус

Django: 8111 passed, 0 assertion failures, 2 import errors, 553 skipped, total8666. Node12/12; Ruff passed. 208 full JSON/HTML semantic comparisons;18 rollback JSON pairs; browser50 page/theme/viewport states +12 controls, expanded filters2; server pagination140 checks; real ZAP3×201 +dedup, actual CSRF create/edit/login and two vulnerability references. Проверки выполнены реально, не выведены из HTTP200/count alone.

Два blockers не исправлены добавлением новых интеграций или изменением дедупликации. См. [test results](RC2_TEST_RESULTS.md), [known issues](RC2_KNOWN_ISSUES.md), [gates](RC2_RELEASE_CHECKLIST.md). Кандидат можно исследовать локально на48091; статус «Release Ready»/Stable не присвоен.

## Исходники, доставка, rollback

App ID `sha256:40ccfda81142aa8482d0b05fb501684c3bc23df231169a069a02e1da51052f0c`; nginx ID `sha256:82851226dc47f5756dc7d56fea0f43c851bc9e86df63682a549802875f06c411`. Локальные images, registry digest отсутствует. Проверено2233 app files/40 static files, reproducible content IDs; [provenance](RC2_GIT_PROVENANCE.md). RC1 HEAD/source различались из-за QA/packaging/docs, embedded runtime не расходился.

Список изменений: [changed files](rc2/changed_files.md). [Reproduce](rc2/REPRODUCE.md), [build](BUILD.md), [deployment](DEPLOY.md), [rollback](ROLLBACK.md). Никаких destructive DB операций или изменения исходных findings. Следующие400-findings/10VU и external-node испытания не выполнялись и остаются отдельным этапом.
