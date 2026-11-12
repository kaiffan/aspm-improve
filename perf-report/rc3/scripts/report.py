"""Render the final report only after the entire accepted candidate passed."""
import collections
import hashlib
import json
import math
import re
import statistics
from pathlib import Path

OUT=Path(__file__).resolve().parents[1]
ROOT=OUT.parents[1]


def read(name):
    return json.loads((OUT/name).read_text())


def write(name,text):
    (OUT/name).write_text(text.rstrip()+'\n')


def table(headers,rows):
    def cell(value):return str(value).replace('|','\\|').replace('\n',' ')
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(cell(x) for x in row)+' |\n' for row in rows)


def number(value,digits=3):
    return f'{value:.{digits}f}' if value is not None else 'N/A'


def change(a,b):
    return f'{(b/a-1)*100:+.1f}%' if a else '0'


for marker in ['campaign-complete','sql-audit-complete','validation-complete']:
    assert read('raw/'+marker+'.json')['complete'],marker
tests=read('raw/full-final-tests.json')
assert tests['errors']==tests['assertion_failures']==tests['wrapper_exit_code']==0
assert tests['skipped']==553
rows=read('benchmark_results.json')
assert sum(r['n'] for r in rows)==14640
build=read('raw/build-final.json')
assert tests['source_sha']==build['source_sha']
assert all(row['only_csrf_and_warning_time_change'] for row in read('raw/html-dynamic-size-check.json'))
main={(r['variant'],r['concurrency']):r for r in rows if r['phase']=='campaign'}
a,b=main['rc2',25],main['rc3',25]
assert a['n']==b['n']==900 and a['repeats']==b['repeats']==3
endpoints={(r['variant'],r['case']):r for r in rows if r['phase']=='endpoints'}
metrics=[('Mixed p50, s','p50_ms',1000),('Mixed p90, s','p90_ms',1000),('Mixed p95, s','p95_ms',1000),('Mixed p99, s','p99_ms',1000),('Throughput, RPS','rps',1),('PostgreSQL sampled CPU, %','pg_cpu_mean_pct',1),('App container peak, MiB','app_rss_peak_mib',1),('SQL execute wall/request, ms','sql_wall_mean_ms',1)]
final_table=table(['Показатель','RC2','Optimized RC3','Изменение'],[(label,number(a[key]/scale),number(b[key]/scale),change(a[key],b[key])) for label,key,scale in metrics]+[('HTTP errors','0','0','0')])
repeat_table=table(['Variant','Repeat p95, s','Repeat RPS'],[(variant,', '.join(number(x['p95_ms']/1000) for x in main[variant,25]['runs']),', '.join(number(x['rps']) for x in main[variant,25]['runs'])) for variant in ['rc2','rc3']])

# Full JSON and meaningful template contexts, with expected permission denials.
before={(r['actor'],r['case']):r for r in read('raw/profile-final-rc2.json')}
after={(r['actor'],r['case']):r for r in read('raw/profile-final-rc3.json')}
assert before.keys()==after.keys()
compat=[]
for key,left in before.items():
    right=after[key]
    equal=left['status']==right['status'] and left.get('payload_hash')==right.get('payload_hash') and left.get('semantic')==right.get('semantic')
    compat.append({'actor':key[0],'case':key[1],'status':left['status'],'full_json':bool(left.get('payload_hash')),'equal':equal})
assert all(row['equal'] for row in compat),[row for row in compat if not row['equal']]
(OUT/'raw/compatibility.json').write_text(json.dumps(compat,indent=2)+'\n')
json_pairs=sum(row['full_json'] for row in compat)
html_pairs=len(compat)-json_pairs
before_integrity=read('raw/integrity-before-load.json')
after_integrity=read('raw/integrity-final.json')
for db in ['source','dd_round4_seed']:
    for key in ['count','sum_ids','full_row_xor','sha256_of_ordered_row_sha256','max_updated']:
        assert before_integrity[db][key]==after_integrity[db][key],(db,key)

targets=b['p95_ms']<=3000 and b['rps']>=20 and b['p99_ms']<a['p99_ms']
ranking=(OUT/'BOTTLENECK_RANKING.md').read_text().split('\n## Final retained decisions')[0]
ranking+='\n## Final retained decisions\n\n'+table(['Component','Measured final result','Decision'],[
    ('Scoped authorization',f"Mixed c25 p95 {a['p95_ms']/1000:.3f}→{b['p95_ms']/1000:.3f} s; RPS {a['rps']:.3f}→{b['rps']:.3f}",'Retained; 3 paired repeats, unchanged mix'),
    ('Findings UI page/autocomplete',f"Standalone p95 {endpoints['rc2','web_findings']['p95_ms']/1000:.3f}→{endpoints['rc3','web_findings']['p95_ms']/1000:.3f} s",'Retained; n=160/build, guarded query shapes'),
    ('Test UI page/autocomplete',f"Standalone p95 {endpoints['rc2','web_test']['p95_ms']/1000:.3f}→{endpoints['rc3','web_test']['p95_ms']/1000:.3f} s",'Retained; exact count and complex-filter fallback'),
    ('Dashboard counter batching','All 3 incremental p95 pairs worsened','Rejected and reverted'),
    ('Indexes/runtime/Celery','No demonstrated need for configuration/index change','Unchanged; no speculative tuning'),
])
write('BOTTLENECK_RANKING.md',ranking)
write('EXECUTIVE_SUMMARY.md',f'''# ASPM 1.0.1 RC3 — итог

{'Целевые ориентиры достигнуты' if targets else 'Измеренный результат; часть stretch goals не достигнута'} в новой сопоставимой серии.
RC2 runtime: `25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb`; release HEAD:
`9384826c2c2ccdbf0178ebc3faa5ea3e5513473d`. RC3 runtime:
`{build['source_sha']}`. Ветка `perf/1.0.1-rc3-optimization`.

{final_table}

По 900 c25 observations на вариант, три независимых повтора; A/B, B/A, A/B.
Дополнительно c1/5/10/15, standalone-маршруты и промежуточный вариант:
всего 14 640 измеренных запросов основной принятой кампании, все HTTP 200.
Серверный SQL-аудит на отдельной PostgreSQL-копии учитывается отдельно.
Суммарный sampled CPU и container peak не обязаны падать при росте throughput;
их фактические изменения в таблице не скрыты.

Основная причина tail latency — повторное чтение heap Finding для каждого
авторизованного Test. SQL InitPlan по Test PK устраняет эти повторные проходы,
сохраняя membership/privileged-action gates. Для Findings/Test UI сначала
выбирается упорядоченная страница, затем считаются endpoint-аннотации. Capped
autocomplete сохраняет разрешённую проекцию до DISTINCT. Сортировки через связи
и фильтры с размножающим to-many JOIN используют прежний путь: отдельные
regression tests обнаружили и закрыли оба случая изменения границ страницы.

Объединение Dashboard counters **отклонено**: три парных повтора ухудшили p95.
Нет новых индексов, materialized counters, migrations, dependency или runtime
tuning. Full Products payload, точные counts, sorting и права сохранены.

Full Django suite: **{tests['tests_run']} run / {tests['passed']} passed /
0 failures / 0 errors / 553 прежних skipped**. Оба import blocker исправлены
реальными upstream-реализациями; 12/12 JavaScript tests passed. Полные JSON API:
{json_pairs} пар; UI contexts: {html_pairs} пар; расхождений 0. Реальные browser,
import/reimport/dedup/evidence, pagination и image rollback результаты перечислены
в [TEST_RESULTS](TEST_RESULTS.md).

Оригинал и protected seed: 1 000 168 findings, сумма ID 500168514196,
полный row SHA-256 fingerprint неизменён. Все writes — на отдельной копии.
Локальные Docker image IDs: [build manifest](raw/build-final.json).
Stable не публикуется; ограничения и воспроизведение см. [RESULTS](RESULTS.md),
[REPRODUCE](REPRODUCE.md), [ROLLBACK](ROLLBACK.md).
''')

levels=[]
for c in [1,5,10,15,25]:
    left,right=main['rc2',c],main['rc3',c]
    levels.append((c,number(left['p95_ms']/1000),number(right['p95_ms']/1000),change(left['p95_ms'],right['p95_ms']),number(left['rps']),number(right['rps']),change(left['rps'],right['rps'])))
endpoint_rows=[]
for case in sorted({r['case'] for r in rows if r['phase']=='endpoints' and r['variant']=='rc2'}):
    left,right=endpoints['rc2',case],endpoints['rc3',case]
    endpoint_rows.append((case,160,number(left['p95_ms']/1000),number(right['p95_ms']/1000),change(left['p95_ms'],right['p95_ms']),number(left['sql_wall_mean_ms']),number(right['sql_wall_mean_ms']),number(left['response_bytes_mean'],1),number(right['response_bytes_mean'],1)))
ui_control_rows=[]
for case in ['web_findings','web_test']:
    for variant in ['rc2','fix1','rc3']:
        row=endpoints[variant,case]
        ui_control_rows.append((case,variant,number(row['by_case'][case]['mean_ms']/1000),number(row['p50_ms']/1000),number(row['p95_ms']/1000),number(row['rps']),number(row['sql_wall_mean_ms'])))
write('RESULTS.md',f'''# Fresh paired results

{final_table}

{repeat_table}

{table(['Concurrency','RC2 p95 s','RC3 p95 s','p95 change','RC2 RPS','RC3 RPS','RPS change'],levels)}

Each level has 300 measured +25 warmup requests per run, 3 repeats/build. Same
25 identities, seeds, case/actor schedule, full Product payload, database,
statistics, dependency images, uWSGI 4×4 and Docker limits. RPS=ΣN/Σelapsed;
percentiles pool observations. These are fixed-count saturation tests with a
drain period, not a production steady-state SLA. Three pairs establish a large
repeatable observed effect here; no claim of universal statistical significance.
Actor/case schedules and all API response byte sizes match exactly in every
pair. Existing HTML session-warning floating timestamps vary by at most 2 bytes
within each actor/route pair; this also occurs within a build. No padding or
payload reduction is applied. See `raw/cohort-verification.json` and the repeated
render check `raw/html-dynamic-size-check.json`; full semantic contexts also match.

## Standalone endpoints

{table(['Case','n/build','RC2 p95 s','RC3 p95 s','Change','RC2 SQL wall ms','RC3 SQL wall ms','RC2 bytes','RC3 bytes'],endpoint_rows)}

Endpoint p95 uses n=160; endpoint p99 is not asserted below n=300. Small changes
on fast routes remain visible and are not treated as proven regressions or wins.
Full Products remains unchanged and its required ID payload remains a material
cost. Findings UI and Test UI are standalone only, never inserted into the mix.

## Incremental UI controls

{table(['Route','Variant','Mean s','p50 s','p95 s','RPS','SQL wall ms/request'],ui_control_rows)}

`fix1` is authorization-only. Its small-scope global title-index walk can worsen
mean/throughput even when p95 improves; that intermediate regression is retained
here. The final UI fixes are evaluated against both RC2 and this intermediate
control. No lower intermediate p95 is presented as proof that every request won.

## Excluded or rejected cohorts

* `raw/rejected-dashboard/`: all 3 adverse incremental pairs and the deliberately
  stopped partial campaign; no samples selected out of a final run.
* `raw/pre-related-order-guard/`: the entire earlier successful 14,640-request
  candidate, retained after a separate edge-case test found related-sort page
  duplication. The final table uses the new guarded build, not those numbers.
* `raw/pre-multivalued-filter-guard/`: the complete subsequent 14,640-request
  cohort at 49066c037bc38a3795cad00ded7dd95f2fd16c96, superseded by a regression
  test proving a multiplying to-many filter must retain grouping before LIMIT.
* `raw/pre-test-ui-count-guard/`: successful full suite at 6c2e69590c68879e12610f8dcb7c8eb3f700a348
  and the initial authorization-only run. Campaign stopped when a real Test UI
  expired-acceptance test proved count=3 instead of 2; no RC3 comparison reused.
* `raw/interrupted-user-message/`: partial resource/RSS window when the tool
  session was stopped by follow-up input before endpoint JSON serialization.
* Tracing/cProfile and isolated pg_stat_statements HTTP observations are diagnostic
  cohorts, never pooled with the primary latency series.

CPU values are sampled and 100%=one core; app memory is Docker container memory,
not summed worker RSS. SQL execute wall includes waiting/network, not just PG
execution. Full raw observations, errors, resource windows and repeat results
are retained in `raw/`, CSV and JSON. Missing resource values stay N/A.
The c25 measured windows contain {a['resource_samples']} RC2 and
{b['resource_samples']} RC3 resource samples; these short fixed-count runs give
coarse CPU estimates, not a steady-state utilization or capacity certification.

![Mixed p95](charts/mixed-p95-vs-concurrency.png)
![Throughput](charts/rps-vs-concurrency.png)
![Standalone p95](charts/slow-endpoint-p95.png)
![Distribution](charts/response-time-distribution.png)
![Rejected experiment](charts/rejected-dashboard-batching.png)
''')

environment=read('raw/environment.json')
settings=environment['settings']
write('SYSTEM_AUDIT.md',f'''# System and provenance audit

RC2 remote release ref was verified before edits at full SHA
`9384826c2c2ccdbf0178ebc3faa5ea3e5513473d`; runtime source is
`25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb`. The original feature checkout and
uncommitted user files were not edited. Work is on a separate release-based
worktree/branch, as explicitly requested for this fork.

Accepted RC3 runtime `{build['source_sha']}`; app `{build['images']['app']['id']}`;
gateway `{build['images']['nginx']['id']}`. Both builds use the checked-in immutable
dependency image digest lock, GNU msgfmt and Git archive. No application library
update or frontend asset change. Full dependency versions: `raw/environment.json`.
Runtime file/image verification: `raw/provenance.json`.

Docker: {environment['docker']['NCPU']} logical CPUs,
{environment['docker']['MemTotal']/1024**3:.3f} GiB VM RAM,
{environment['docker']['Architecture']}, {environment['docker']['OperatingSystem']},
engine {environment['docker']['ServerVersion']}. No per-container CPU/memory
limits; DEBUG={settings['debug']}; CONN_MAX_AGE={settings['conn_max_age']}.
uWSGI 4 processes ×4 threads. Original demo/worker were stopped for both builds.
Power, host free memory, swap, OOM and all relevant containers were sampled.
Baseline host swap snapshot: `{environment['swap'].strip()}`. This differs from
historical snapshots and is another reason not to reuse historical Round 5/RC1
performance numbers. Current A/B uses the same host conditions and guards.

PostgreSQL 18.6, shared_buffers 128 MiB, work_mem 4 MiB,
default_statistics_target 100, max_connections 100, max_parallel_workers_per_gather
2, JIT on. The primary server has empty shared_preload_libraries and IO timing off.
Its settings/statistics are not changed. The separate SQL-audit copy enables
pg_stat_statements and IO timing, restores identical rows, ANALYZEs once before
either build and retains the same audit statistics for both. Its timings are
explicitly separate from primary HTTP measurements.

Integrity includes every Finding field, count, ID sum, full-row XOR, max_updated
and SHA-256 over ordered row SHA-256 values. Source and seed match before and after:
`{after_integrity['source']['sha256_of_ordered_row_sha256']}`.
No destructive migrations, DROP, volume deletion, source write tests or force push.
''')

route_rows=[]
for case,route in sorted(a['by_case'].items(),key=lambda kv:kv[1]['request_elapsed_ms'],reverse=True):
    route_rows.append((case,route['n'],number(route['p50_ms']/1000),number(route['p90_ms']/1000) if route['p90_ms'] else 'N/A',number(route['p95_ms']/1000) if route['p95_ms'] else 'N/A',number(route['mean_ms']/1000),number(route['request_elapsed_ms']/1000),number(route['request_elapsed_share']*100,1)+'%',number(route['sql_count_mean'],1)+' / '+str(route['sql_count_max']),number(route['sql_wall_mean_ms']),number(route['bytes_mean'],1),number(route['share_of_slowest_five_percent']*100,1)+'%'))
profiles=list(before.values())
costs=collections.defaultdict(list)
for row in profiles:costs[row['case']].append(row)
top=sorted(costs.items(),key=lambda kv:sum(r['wall_ms'] for r in kv[1]),reverse=True)[:10]
top_rows=[(rank,case,len(items),number(statistics.mean(r['wall_ms'] for r in items)),number(sum(r['sql_ms'] for r in items)),number(statistics.mean(r['sql_count'] for r in items),1),max(r['sql_count'] for r in items)) for rank,(case,items) in enumerate(top,1)]
process_groups=collections.defaultdict(list)
for variant in ['rc2','rc3']:
    for item in read(f'raw/process-{variant}.json'):
        process_groups[variant,item['case']].append(item)
process_rows=[(variant,case,len(items),number(statistics.mean(r['cpu_with_tracing_ms'] for r in items)),number(statistics.mean(r['python_peak_allocated_bytes'] for r in items)/1024**2),number(max(r['rss_after_kib'] for r in items)/1024)) for (variant,case),items in sorted(process_groups.items())]
dashboard_components=[]
for variant,source in [('rc2',before),('rc3',after)]:
    for item in source.values():
        if item['case']!='dashboard':continue
        parts=item.get('template_context_components',[])
        render=[r['cumulative_s']*1000 for r in parts if r['function']=='render']
        processors=[r for r in parts if 'context_processor' in r['file']]
        dashboard_components.append((variant,item['actor'],number(item['wall_ms']),number(item['sql_ms']),item['sql_count'],number(max(render)) if render else 'N/A',number(sum(r['own_s'] for r in processors)*1000)))
write('DJANGO_ANALYSIS.md',f'''# Django and route delay map

## RC2 mixed c25 route contribution

{table(['Route','Calls','p50 s','p90 s','p95 s','Mean s','Summed elapsed s','Elapsed share','SQL mean/max','SQL wall ms/request','Mean bytes','Share of slowest 5%'],route_rows)}

Small route samples do not support p95; the standalone table in RESULTS supplies
n=160 per endpoint. p99 requires n≥300. Summed request elapsed overlaps across
requests and is **not CPU share**. CPU/RSS/allocation snapshots are separate in
`raw/process-rc2.json` / `raw/process-rc3.json`, n=1 diagnostic per route/actor,
with tracemalloc overhead; no HTTP percentile is inferred from them.

## TOP-10 equal-count diagnostic routes

{table(['Rank','Route','Calls/actors','Mean view+render ms','Total SQL wall ms','Mean SQL','Max SQL'],top_rows)}

This c1 diagnostic table has four named actors per route. It is a call-cost map,
not a substitute for mixed workload weights or a per-route p95 estimate.

## Separate CPU/allocation/RSS diagnostics

{table(['Build','Route','Actors (n=1 each)','Mean traced process CPU ms','Mean peak Python allocations MiB','Max process RSS after MiB'],process_rows)}

These traced measurements include diagnostic overhead and run in a separate
Django process. They measure application CPU, not database CPU or concurrent
worker utilization; rows cannot be summed into production load.

## Dashboard view, SQL and template components

{table(['Build','Actor','View+render ms','SQL wall ms','SQL count','Max nested template render ms','Context processor self ms'],dashboard_components)}

Template render is the maximum inclusive nested render call, not a sum of
overlapping template calls. Context processor self time excludes child calls;
their complete inclusive/self timings are retained separately in each profile.
Every aggregate's SQL execution wall and Django caller stack are in sql-final
raw records; EXPLAIN execution times are server-only diagnostic replays.

Dashboard: view time includes the exact recent counts, one day/severity chart
aggregate and rendering. cProfile records template and context-processor calls
individually in `raw/profile-final-*.json`. The hot scoped chart/counter scans
previously revisited the Finding heap once per Test; authorization InitPlan now
resolves that scope once. Original chart boundaries, unknown severities, risk
acceptance uniqueness and timezone behavior remain guarded by R4/R5 tests. The
counter-batching experiment was rejected, so the exact counters remain separate.

Findings UI: title suggestions and CWE options are lazy QuerySets evaluated while
building filters/context; endpoint annotations previously grouped the full scope
before LIMIT. The selected PK page now precedes those annotations for local-field
sorts. Linked notes, Jira, vulnerability IDs, endpoints and evidence prefetches
remain. Related/random/custom orderings retain the original grouping/LIMIT path.
The new related-sort test proves one Finding with two acceptance dates does not
inflate a page of size one. A second test reproduces duplicate PKs before LIMIT
from a to-many filter: these joins retain the original annotation-before-page
path. The existing shared join detector is reused unchanged, with a compatible
import from dojo.filters. Projections, custom extra SQL, groups and combinations
also retain the original path.

Test UI: pagination/counting now precedes Finding prefetch annotations, matching
the list view's intended sequence for safe query shapes. Related ordering and
multiplying filters retain annotation/grouping before counting and pagination;
the expired-acceptance test verifies exact count=2 with overlapping acceptances.
Its product-tab exact open count and global
authorized autocomplete remain material costs. Notes/files/Jira/finding-group
template loops remain functionally unchanged and are checked by full suite and
real browser tests. Query count alone is not treated as the bottleneck.

Products full API still emits the complete ordered active ID lists and exact
counts. Products UI, detail, Tests, Engagements and Endpoints retain their response
and permission contracts. Reports builder is audited in the separate CPU/allocation
and view profiles and the actual browser run; report unit/integration cases are in
the full suite. Fast low-impact endpoints receive no speculative optimization.

![Incremental UI effect](charts/before-after-ui-fixes.png)
''')

sql_sections=[]
for variant in ['rc2','rc3']:
    native=[r for r in read(f'raw/pg-stat-statements-{variant}-c25.json') if 'pg_stat_statements' not in r['query']][:10]
    sql_sections.append('## '+variant.upper()+' server TOP-10, c25\n\n'+table(['ID','Calls','Total exec ms','Mean exec ms','Rows','Shared hit/read','Temp read/write'],[(f'Q{i}',r['calls'],number(r['total_exec_time']),number(r['mean_exec_time']),r['rows'],str(r['shared_blks_hit'])+'/'+str(r['shared_blks_read']),str(r['temp_blks_read'])+'/'+str(r['temp_blks_written'])) for i,r in enumerate(native,1)]))
    for i,row in enumerate(native,1):
        sql_sections.append(f"### {variant.upper()} Q{i}\n\n```sql\n{row['query']}\n```\n")
    diagnostic=collections.defaultdict(list)
    plans=collections.defaultdict(list)
    for item in read(f'raw/sql-final-{variant}.json'):diagnostic[item['sql']].append(item)
    for item in read(f'raw/plan-final-{variant}.json'):plans[item['sql']].append(item)
    inventory=[]
    for statement,items in sorted(diagnostic.items(),key=lambda pair:sum(r['ms'] for r in pair[1]),reverse=True)[:10]:
        candidates=plans[statement]
        chosen=max(candidates,key=lambda row:row['query_ms']) if candidates else None
        text=chosen['plan'] if chosen else ''
        execution=re.search(r'Execution Time: ([\d.]+) ms',text)
        buffers=next((line.strip() for line in text.splitlines() if 'Buffers:' in line),'N/A')
        loops=[int(value) for value in re.findall(r'loops=(\d+)',text)]
        callers=sorted({frame for row in items for frame in row['stack'] if any(name in frame for name in ['/queries.py:','/views.py:','/utils.py:','/filters.py:','/query_registrations.py:'])})
        inventory.append({'query_id':hashlib.sha256(statement.encode()).hexdigest()[:12],'sql':statement,'calls':len(items),'total_execute_wall_ms':sum(r['ms'] for r in items),'routes':sorted({r['case'] for r in items}),'callers':callers,'representative_server_execution_ms':float(execution[1]) if execution else None,'representative_root_buffers':buffers,'max_plan_loops':max(loops) if loops else None,'plan_actor':chosen['actor'] if chosen else None})
    write(f'raw/sql-callsite-index-{variant}.json',json.dumps(inventory,indent=2))
    sql_sections.append('## '+variant.upper()+' diagnostic call-site/plan index\n\n'+table(['Shape ID','Routes','Calls / total wall ms','Representative server ms','Root buffers','Max loops','Django callers'],[(r['query_id'],', '.join(r['routes']),str(r['calls'])+' / '+number(r['total_execute_wall_ms']),number(r['representative_server_execution_ms']),r['representative_root_buffers'],r['max_plan_loops'],', '.join(r['callers'])) for r in inventory])+'\n\nThis equal-count c1 diagnostic index is separate from native mixed pg_stat_statements totals. Server times replay bound parameters; root buffers are inclusive, never summed over nested nodes. Full SQL and caller details are retained in sql-callsite-index JSON.\n')
sql_levels=[]
for c in [1,10,25]:
    for variant in ['rc2','rc3']:
        data=[r for r in read(f'raw/pg-stat-statements-{variant}-c{c}.json') if 'pg_stat_statements' not in r['query']]
        sql_levels.append((variant,c,sum(r['calls'] for r in data),number(sum(r['total_exec_time'] for r in data)),sum(r['shared_blks_read'] for r in data),sum(r['temp_blks_written'] for r in data)))
write('SQL_ANALYSIS.md','''# PostgreSQL audit

Primary latency/SQL execute wall comes from the unchanged retained server.
Server cumulative execution totals below come from **pg_stat_statements on a
separate streamed copy**, with the same PostgreSQL image, row fingerprint,
configuration for both builds and one ANALYZE before either build. Only that
copy enables pg_stat_statements/IO timing. Source is never restarted or tuned.
Each server-stat window includes 300 measured +25 warmup HTTP requests; it is not
pooled into primary latency/RPS. Raw native rows include calls, execution, buffers,
temp IO, rows, WAL and available IO timing. No parameters/credentials are logged.

'''+table(['Build','Concurrency','SELECT calls','Total exec ms','Shared read','Temp blocks written'],sql_levels)+'\n\n'+'\n\n'.join(sql_sections)+'''

## Call sites and plans

All expensive SELECTs have caller stacks and individual execute wall observations
in `raw/sql-final-rc2.json` / `raw/sql-final-rc3.json`. Corresponding actual plans:
`raw/plan-final-rc2.json` / `raw/plan-final-rc3.json`, using
`EXPLAIN (ANALYZE, BUFFERS, VERBOSE, TIMING OFF)`. TIMING OFF avoids per-node
clock overhead but retains actual rows/loops, buffers and total Execution Time.
The initial profiles/plans and autocomplete alternative plans are retained too.

* Dashboard counts: `dojo/home/views.py:dashboard`; three exact recent counters
  and one day/severity aggregate per request. DISTINCT is retained for exact
  unique Findings where a risk-acceptance join can fan out. Removing all DISTINCT
  would change correctness. Authorization formerly exposed per-Test heap scans:
  the large scoped chart read ~482,300 shared buffers over eight scans. The InitPlan
  retains every permission gate and visits the Finding heap without that outer join.
* Filtered Findings: `ApiFindingFilter.filter_product` plus scoped ViewSet; exact
  count and ordered page per request. Previously 63,688 matching wide rows were
  sorted for 100 results and the heap was revisited for each Test. The selected
  product Test-array filter is retained, now intersecting an authorized Test array
  instead of an outer Finding→Test→Engagement permission join.
* UI: `prefetch_for_findings` endpoint annotations previously grouped 532,569 rows
  for a page of 25; the PK page is now an IN subquery before grouping, in one SQL
  snapshot. Related ordering, multiplying outer joins and unsupported query
  shapes deliberately retain the original path, with behavioral regression tests.
* Autocomplete: `get_words_for_field`; bounded DISTINCT title/component values,
  not a template N+1. The first array-only candidate walked a global title index,
  rejected ~574,613 unrelated rows for a small scope, and regressed standalone UI.
  The authorized projection barrier changed that measured plan from ~1.240 s to
  ~0.049 s. The same unordered DISTINCT/LIMIT semantics and bound parameters remain;
  no global permission-sensitive cache is introduced. A large-scope hash aggregate
  can still spill; it is not hidden or replaced with incomplete counts.
* Products: `ProductViewSet._load_findings_fields`; exact ordered ARRAY_AGG IDs
  once per authorized page. The output itself is large and remains unchanged.
* Test UI: product-tab open count, filters, notes/Jira/evidence prefetches and
  endpoint annotations. These are separately visible in caller stacks/plans.

Small-table sequential scans and broad sequential scans with lower total cost
are not errors by themselves. No planner hint, disabled plan node, global work_mem
increase, new index or statistics manipulation is used to manufacture a win.
Shared buffer reads are not necessarily physical storage reads. Locks/waits are
sampled separately; they are not summed into CPU utilization. Residual expensive
work includes exact counts, full Product ID materialization, and broad aggregates.

![Server SQL RC2](charts/server-top-sql-rc2.png)
![Server SQL RC3](charts/server-top-sql-rc3.png)
''')

wait_rows=[]
for path in (OUT/'raw').glob('campaign-*-worker-wait.json'):
    data=json.loads(path.read_text());samples=data['samples']
    if samples:
        wait_rows.append((data['run'],len(samples),number(statistics.mean(s['worker_ms'] for s in samples)),number(statistics.mean(s['queue_proxy_network_residual_ms'] for s in samples)),number(max(s['completion_match_error_ms'] for s in samples))))
task_rows=[json.loads(line) for line in (OUT/'raw/celery-tasks.jsonl').read_text().splitlines() if line]
task_groups=collections.defaultdict(list)
for row in task_rows:task_groups[row['task']].append(row)
celery=table(['Task','Calls','States','Mean execution ms','Max execution ms','Mean eligible queue wait ms','Peak process RSS MiB'],[(task,len(items),dict(collections.Counter(r['state'] for r in items)),number(statistics.mean(r['execution_ms'] for r in items)),number(max(r['execution_ms'] for r in items)),number(statistics.mean(r['queue_eligible_wait_ms'] for r in items if r['queue_eligible_wait_ms'] is not None)) if any(r['queue_eligible_wait_ms'] is not None for r in items) else 'N/A',number(max(r['process_peak_rss_kib'] for r in items)/1024)) for task,items in sorted(task_groups.items())])
write('RUNTIME_ANALYSIS.md',f'''# Runtime audit

No runtime tuning was retained. uWSGI remains 4×4; CPU/RAM limits, connection age,
backlog, recycling and middleware are unchanged. Startup/cmdline evidence is in
`raw/runtime-final.json`; the exact middleware list and PG settings are in
`raw/environment.json`. Connection maxima, wait samples, swap/free memory, OOM,
container memory and each real worker RSS are retained per run. At c25, sampled
PG CPU was {number(a['pg_cpu_mean_pct'])}%→{number(b['pg_cpu_mean_pct'])}% and app CPU
{number(a['app_cpu_mean_pct'])}%→{number(b['app_cpu_mean_pct'])}%. Throughput rises while
total busy CPU remains high; no reduction in total CPU is falsely asserted.

## Worker service time and residual

{table(['Run','Matched','Mean worker ms','Mean queue+proxy+network residual ms','Max timestamp matching error ms'],wait_rows)}

Access logs match identical actor, URL, response bytes/status and nearest completion
within 250 ms. The residual is an upper-bound style diagnostic including proxy,
transport and queueing; it is not an exact exclusive queue wait. Windows whose
container logs were already replaced are N/A, never zero. No worker count increase.

## Celery on the isolated write copy

Pool=prefork, concurrency=1, autoscale=1/1, prefetch multiplier=1, matching the
retained validation worker. Publish→start timing uses diagnostic headers; eligible
wait subtracts an intentional ETA/countdown. Execution is measured separately,
and RSS is each process's cumulative high-water mark, not per-task allocated RAM.

{celery}

These are actual import/reimport/dedup/grade tasks on the validation copy, not a
claim about every scanner or million-row import. The primary mixed workload is
read-only with no worker/beat and a zero task queue. Celery/broker was not its
bottleneck, so neither configuration is changed. Diagnostic hooks and SQL middleware
are removed before leaving the candidate demo running.

![PG CPU](charts/postgresql-cpu.png)
![PG waits](charts/postgresql-waits.png)
![App CPU](charts/worker-cpu.png)
![Worker RSS](charts/worker-rss.png)
''')

skip_reasons=collections.Counter(row['reason'] for row in tests['skip_details'])
coverage=['test_round4_performance','test_round5_performance','test_api_finding_relation_filters','test_api_finding_filter_no_multiply','test_local_release_performance_checks','test_api_product_prefetch','test_apiv2_prefetch_test_finding_groups','test_rc2_product_filters','test_ui_pagination_hardening','test_rc3_finding_scope','test_rc3_finding_page','test_ticket_comments','test_trufflehog_parser']
coverage_rows=[(name,sum(name+'.' in test for test in tests['passed_ids'])) for name in coverage]
browser=read('raw/browser-validation.json')
assert not browser['failures']
matrix=read('raw/ui-matrix.json')
rollback=read('raw/rollback-check.json')
assert not matrix['failures'] and all(row['equal'] for row in rollback['comparisons'])
write('TEST_RESULTS.md',f'''# Accepted-candidate validation

Sanctioned `./run-unittest.sh --test-case unittests`, offline test PostgreSQL and
read-only source mounts, runtime source `{tests['source_sha']}`:
**{tests['tests_run']} run; {tests['passed']} passed; 0 failures; 0 errors;
553 skipped**. Full method outcomes/skip reasons: `raw/full-final-tests.json`.
JavaScript: 12/12 passed, 0 failures/skips (`raw/javascript-tests.log`). Frontend
packages define build scripts but no additional test command.

Both original import errors are reproduced with full tracebacks in
`raw/discovery-red.log`, and resolved by restoring actual upstream implementations,
not test exclusions/stubs. `raw/discovery-green.log` proves full module loading.
The first post-blocker suite exposed one separate concurrent-index fixture timing
race; its traceback and the failed summary are retained. The fixture now releases
the snapshot on observed polling, with unchanged production migration code.

{table(['Guard/module','Passed methods in full suite'],coverage_rows)}

This covers retained Round 1–5 API/query/prefetch/pagination guards, RC2 filters,
Product/Finding permissions, import/reimport, dedup, evidence and reports. The new
scope guard fails on RC2 and passes on RC3; the related-sort and to-many-filter
page guards first reproduced changed page rows and pass after conservative
fallbacks. Their original failures and focused green outcomes are retained.
Ruff 0.16.10 passes changed production/tests; check/migration dry-run/schema
management results are in `raw/management-checks.json`. No new migration.

## Real API, browser and writes

* {len(compat)} before/after profile pairs: {json_pairs} complete JSON hashes and
  {html_pairs} meaningful template context comparisons; mismatches=0, including
  expected restricted users/notes 403 results.
* Browser: {len(browser['rows'])} page/theme/viewport states,
  {len(browser['checks'])} functional checks; failures=0. Real Playwright/Chromium,
  axe, Light/Dark/System, keyboard/sidebar, Select2, selection and rapid navigation.
  Screenshots live in `screenshots/`. No CSS/SVG/palette/navigation rewrite.
* Server pagination matrix: {matrix['checks']} checks, failures=0: first/next/prev/
  last, malformed/negative/huge page, page sizes, filters/sort/empty results,
  Test prefix and admin/restricted identities.
* Real ZAP import/reimport/duplicate-peer: three 201 responses with completed
  dedup. Primary 44 scanner findings, 4 mitigated; peer 40/40 duplicates. Actual
  locations/evidence and two linked vulnerability IDs are checked, along with
  CSRF create/edit, invalid/valid login and no-access denial on the isolated copy.
* Actual RC2→RC3 image rollback: {rollback['pairs']} complete JSON pairs equal,
  worker stopped for switching and candidate restored. Separate DB/media only.

## Unchanged skip reasons and scope limits

{table(['Count','Existing reason'],[(count,reason) for reason,count in skip_reasons.most_common(8)])}

All 553 reasons are in JSON. No skip/xfail is added and no original test is removed.
Experimental Dashboard-only guards are reverted with the rejected optimization;
the original behavioral R4/R5 tests remain. Legacy Selenium/chromedriver is not
claimed executed; actual browser verification uses the pinned Playwright stack.
No 20-million-row, huge Test-count tenant, external-node/HA, or prolonged production
soak is certified by this local candidate validation.
''')

write('FIXES.md','''# Retained fixes and rejected experiments

## Release gate — independent commits

`b2d79aa1e78aee6a555e307830732ac73a2705cf` restores the real upstream
ticket-comment hook/callers and TruffleHog helper/settings. The root cause is a
partial fork integration: newer tests remained while their implementations did
not. No library, dependency or fixture substitute can supply those missing
functions. Full tracebacks, upstream SHAs and semantics are in
`RELEASE_GATE_FIXES.md`. Original default dedup fields/algorithm remain; optional
stable-ID semantics are documented for sites explicitly selecting that algorithm.
`a7da999878` separately fixes only the concurrent-index test's Timer race.

## Authorization — `8492b41e23fa4cdb71391c4712e08124f0172289`

1. Root cause: an outer Finding→Test→Engagement permission join lets PostgreSQL
   revisit heap pages for each authorized Test, with large cardinality error.
2. Before SQL/EXPLAIN: `raw/plan-rc2.json` and `raw/plan-final-rc2.json`; large
   scoped Dashboard has eight Finding heap scans and ~482k buffer accesses.
3. Change: retain anonymous/privileged-action/staff/superuser gates, resolve
   authorized unfiltered Test PKs once via ArraySubquery, then apply test_id=ANY.
   Caller queryset filters and custom registry overrides stay in place.
4. Regression: direct/type/overlapping memberships, caller filtering/order,
   denied actions, anonymous/no-membership, staff bypass and revocation. Red on
   RC2 (`scope-red-corrected.json`), green plus full suite on candidate.
5. After SQL/EXPLAIN: `raw/plan-final-rc3.json`; same authorized results with
   InitPlan and no outer per-Test Finding join.
6. Endpoint before/after: RESULTS; Dashboard/filtered API plus scoped diagnostic
   actors. Complete JSON/context comparisons verify correctness.
7. Mixed before/after: all 30 paired main runs in RESULTS; unchanged workload.
8. Permissions: full authorization/Product/Finding suites, actual no-access
   browser/API cases and full payload hashes; no permission-sensitive global cache.
9. Writes: no schema, index, counter, model-save or import-path change. No new
   write/index maintenance. Test-ID array memory scales with authorized Test count,
   not Finding count; very large Test-count tenants remain an explicit limit.
10. Rollback: ordinary independent revert or exact RC2 images; no schema action.

## UI page and autocomplete — `f21b611ef4888533dfd2252a0c59ed254ae68e67`

1. Root cause: endpoint COUNT annotations GROUP BY the entire Finding scope
   before LIMIT; title DISTINCT may walk a global title index for a small scope.
2. Before plans: initial/final RC2 plans and `raw/autocomplete-alternatives.log`.
   532,569 grouped rows for 25 results; ~574k unrelated title-index rows discarded.
3. Change: one SQL snapshot selects the authorized, filtered, ordered PK page
   before annotation. Test UI paginates before prefetch. A bounded authorized
   projection precedes DISTINCT for Test-array autocomplete scopes; compiler SQL,
   quoted model field and bound values prevent SQL injection or scope widening.
4. Regression: page/order/count, caller non-mutation, evaluated/unsliced behavior,
   exact capped authorized words, revocation and Test UI permissions. The extra
   related-sort guard reproduced two copies of a Finding on a page of size one.
   `49066c037bc38a3795cad00ded7dd95f2fd16c96` retains the original path for related,
   random or custom ordering rather than changing its grouping/cardinality.
   `6c2e69590c68879e12610f8dcb7c8eb3f700a348` applies the same conservative
   fallback to multiplying to-many filters and unsupported query shapes, with
   a separate red/green page-boundary test. The existing join detector is moved
   unchanged to query_utils and remains importable from filters.
   `ccfd52d372695176485e65000b4270e01d7dfb1b` uses the same eligibility guard
   before Test UI counting, preserving count=2 rather than 3 for overlapping
   expired acceptances. Its regression was observed red before the fix and green
   afterwards; both summaries remain in raw/.
5. After plans: final RC3 page GROUP BY is bounded by the PK subquery. Related
   ordering is deliberately not optimized. Capped suggestion semantics stay
   unordered/plan-dependent as before; actual filter predicates are unchanged.
6. Endpoint before/after: both RC2 and authorization-only UI controls, n=160,
   plus final candidate in RESULTS / before-after-ui-fixes chart.
7. Mixed: incremental authorization-only vs retained RC3 runs and the complete
   final main A/B. UI-only routes remain outside the mix.
8. Permissions: original predicates remain inside the subquery and hydration;
   complete actor/context/JSON checks plus real pagination/browser matrix.
9. Writes: none in the optimization; no new index, schema or cache invalidation.
   Real importer/dedup/evidence checks run only on the separate validation copy.
10. Rollback: independent UI revert or RC2 images; all data remains compatible.

## Dashboard batching — rejected

`df254707e70a0dfe467b1a7bc1389efa48d4ca54` combined two exact counters, but all
three incremental pairs worsened mixed p95 while RPS stayed effectively flat.
It was reverted by `e00435fb1e5b2f27e2d793f5a6396c33845cd9a7`. Fewer SQL statements
did not reduce total cost: the merged DISTINCT aggregate lost the advantage of
separate selective paths and increased aggregation work. Every observation is
retained in `raw/rejected-dashboard/`, and no rejected result enters the final table.
Original exact counters remain, accelerated by the retained authorization shape.
''')

write('../../release/1.0.1/RC3_KNOWN_ISSUES.md','''# ASPM 1.0.1 RC3 known issues and measurement limits

* The full suite retains 553 existing skips, including legacy/RBAC and V3-gated
  variants. Their reasons are listed, not hidden. No new skip or loader error.
* Default Product full payload still contains all ordered active Finding IDs;
  exact counts and broad aggregates retain unavoidable cost on large scopes.
* Authorization Test-PK arrays are measured on the million-Finding / roughly
  hundred-Test seed. Tenants with very large Test counts need separate scale
  validation; no claim is made for every cardinality distribution.
* Related/random/custom Finding orderings, multiplying to-many filters and
  unsupported query shapes retain the original annotation/LIMIT path for
  correctness, and therefore do not receive the page-first speedup.
* Autocomplete's existing unordered DISTINCT/LIMIT cap remains plan-dependent.
  Tracemalloc snapshots can show bounded allocation increases; container/worker
  memory is reported separately and no universal memory reduction is claimed.
* Restored TruffleHog stable IDs are additive. Sites explicitly using Unique ID
  from tool should review historical imports before changing dedup configuration.
  Folding remains off; no automatic mass recomputation or data migration.
* Benchmarks are local fixed-count saturation tests. External HA/PostgreSQL,
  long production soak, 20-million-row datasets and legacy Selenium are not
  certified. Runtime worker count, broker, indexes and statistics are not tuned.
* The candidate is a local build, not an automatically published Stable release.
''')
print('Final reports generated; all required gates validated')
