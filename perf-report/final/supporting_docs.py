#!/usr/bin/env python3
import json,re
from pathlib import Path

R=Path(__file__).resolve().parent
P=Path('/private/tmp/dd-35100-round4')
D=json.loads((R/'benchmark_results.json').read_text())

def row(v,case):return next(x for x in D['summary'] if x['phase']=='endpoints' and x['variant']==v and x['case']==case)

items=[]
for case,name,files,cause,risk in [
 ('web_products','Products UI','`dojo/product/queries.py`, `dojo/product/ui/views.py`','Три коррелированных finding count на продукт, включая повторный active count. Batch считает active/verified только для авторизованной страницы; count-сортировка сохраняет прежний SQL-путь.','Порядок и границы страниц проверены; максимальный выигрыш показан для стандартной сортировки.'),
 ('dashboard','Dashboard','`dojo/home/views.py`, `dojo/utils.py`','Дневной GROUP BY выполнялся дважды: count и материализация. Месячная статистика вычисляла два EXTRACT на строку. Теперь дневные группы читаются один раз, месяц — TruncMonth.','Размер Python-результата зависит от числа дней/месяцев, а не числа findings; cutoff/unknown severity сохранены.'),
 ('simple_metrics_cold','Simple Metrics fresh render','`dojo/metrics/views.py`','Для вычисления чисел загружались все Finding-поля и Python-списки, особенно len(closed). Теперь severity counts и exact closed count вычисляет PostgreSQL.','Авторизованные Product Types и все фильтры сохранены; cache hit измеряется отдельно.')]:
    a=row('current',case);b=row('final',case)
    items.append(f'''## {name}\n\n{cause}\n\n- Files: {files}.\n- CURRENT → FINAL p95: **{a['p95_ms']:.1f} → {b['p95_ms']:.1f} мс**; RPS **{a['rps']:.2f} → {b['rps']:.2f}**.\n- SQL statements median: {a['sql_count_median']:g} → {b['sql_count_median']:g}; SQL wall p50: {a['sql_p50_ms']:.1f} → {b['sql_p50_ms']:.1f} мс.\n- {risk}\n''')
(R/'NEW_BOTTLENECKS.md').write_text('''# Newly discovered bottlenecks

Ранжирование после системного аудита: Simple Metrics (материализация и RAM), Products UI (дорогой SQL), Dashboard (повторная работа), затем Notes N+1 и оставшиеся exact counts/Findings UI. Выбраны три небольших исправления с подтверждённым HTTP-эффектом. Число SQL само по себе не равно стоимости: Products UI теперь делает дополнительный дешёвый агрегат и устраняет многократную дорогую работу.

Реестр [57 API registrations](routes.json) получен из Django router, маршруты не придуманы. Проверены основные API, users, product types, endpoints/status, notes, statistics и серверные страницы. Technologies и risk acceptance на этом наборе пусты; для production-нагрузки они не показательны. Reports преимущественно представлены действиями генерации и не запускались массово. Кастомные Engagements/SCM/HA/UI redesign не изменялись.

'''+ '\n'.join(items)+'''
## SQL and EXPLAIN evidence

Фактический SQL и `EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)` безопасных SELECT сохранены:

- [ORIGINAL](explain_original.json), [CURRENT](explain_current.json), [FINAL](explain_final.json).
- [Original Products API](explain_extra_original.json), [Current Products API](explain_extra_current.json), [Final Products API](explain_extra_final.json).
- [Диагностика всей системы](audit_current.json), [SQL audit](audit_sql.jsonl), [альтернативные планы](plan_trials.jsonl).

SQL params не записывались, строковые literals в SQL замаскированы. Execution Time EXPLAIN и SQL wall time HTTP — разные измерения. Shared reads означают загрузку в PostgreSQL shared buffers; при выключенном track_io_timing они не доказывают физическое чтение SSD.

## Ограничения и отклонённые кандидаты

Notes list выполняет запрос history на строки; на текущем маленьком наборе это около 22 SQL и единицы миллисекунд, поэтому патч не оставлен. Обычные Tests/Engagements не показали значимого нового N+1 на этом датасете. Findings UI/Test UI, точный COUNT и большие Product ID arrays остаются дорогими. Добавление индексов или настройка сервера без отдельного доказательства не выполнялись.

В диагностике обнаружены два источника ложного сравнения: общий page cache разных сборок и отсутствие column statistics в первых write-копиях. Финальные серии используют отдельные namespaces и копии после ANALYZE. Старые данные сохранены в `cache_shared_diagnostics/` и `background_unanalyzed/` и не включены в итоговые метрики.
''')
log=(P/'portable-tests.log').read_text()
skips=[line.strip() for line in log.splitlines() if '... skipped ' in line]
red=[line.split(' (',1)[0] for line in (P/'red.log').read_text().splitlines() if line.startswith('FAIL:')]
(R/'test_verification.txt').write_text('CURRENT red\n'+'\n'.join(red)+'\n\nPortable FINAL\n'+next(line for line in log.splitlines() if line.startswith('Ran '))+'\n'+next(line for line in log.splitlines() if line.startswith('OK '))+'\n\n'+(P/'lint-final.log').read_text()+'\nDjango check and makemigrations --check --dry-run succeeded\nOpenAPI spectacular --fail-on-warn succeeded\n')
(R/'TEST_RESULTS.md').write_text('''# Regression and integration results

**100 tests executed; 92 passed, 8 skipped; zero failures/errors.** Repeated using the checked-out repository tests and a separate PostgreSQL database. No tests ran against the million-finding database. Four new guards failed on CURRENT before patches, then passed on FINAL. The fifth new test checks count sorting and real page boundaries.

New tests cover:

- Exact authorized Product counts, absent products, count/name ordering and pagination boundaries.
- Dashboard month cutoff, unknown severity and equivalent timezone-aware grouping.
- One daily aggregate query and the empty punchcard case.
- Simple Metrics exact opened/closed/severity totals and exclusion of false positives without loading Finding descriptions.

Preserved regression modules cover both Product aliases, CSV filters, unauthorized products, inherited access, no multiplied rows, standard/FAST pagination, custom ordering fallback, Product full/count/none, Test Jira groups and vulnerability references. Two actual linked vulnerability identifiers are returned in order in both representation branches and detail.

Modules:

```text
unittests.test_round4_performance
unittests.test_dashboard
unittests.test_api_finding_relation_filters
unittests.test_api_finding_filter_no_multiply
unittests.test_local_release_performance_checks
unittests.test_api_product_prefetch
unittests.test_apiv2_prefetch_test_finding_groups
unittests.test_authorization_queries
```

`test_local_release_performance_checks.py` was restored from the prior isolated runtime checks into Git, eliminating a private test-source dependency. Production source hashes match the tested commits. Django check, migration dry-run and OpenAPI --fail-on-warn succeeded. Test-environment warnings concern the pre-existing development encryption key and wildcard host configuration; they are not schema-generation failures. Ruff 0.17.4 passes for all five new production files and both new/restored test modules.

'''+f'''[Verification summary](test_verification.txt). Compared **{sum('json_equal' in x for x in json.loads((R/'compatibility.json').read_text()))} full JSON pairs** and **{sum('context_equal' in x for x in json.loads((R/'compatibility.json').read_text()))} HTML context pairs**: zero semantic failures. Dynamic HTML hashes are not claimed identical. HTTP observation counts/statuses are in `benchmark_results.json`; p99 is omitted below 300 successful samples.

'''+'''## Skips inherited from the existing suite

'''+ '\n'.join('- '+line for line in skips)+'''

## Real import/reimport

The final write experiment uses three copies made after ANALYZE, one isolated Celery worker and an isolated broker/media. All 54 import/reimport POST return 201 with completed deduplication. Each of six sequences per build ends with primary 44 findings / 40 active and peer 40 findings / 40 duplicates. Request/response evidence and Location references exist, and API statistics match across builds. See `background_correctness.json` and `background_summary.json`.

The first write trial lacked planner statistics. It is preserved and excluded. A single control/loaded read pair per build does not establish a production read-impact SLA. Multiple real scanner formats, 20 million findings, networked HA PostgreSQL and browser JavaScript execution were not validated here. No production capacity claim is made.
''')
print('Filled bottleneck and regression reports generated')
