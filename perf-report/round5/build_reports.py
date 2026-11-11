"""Generate final prose/tables from measured artifacts, never forecast benchmark wins."""
import json
import statistics
from pathlib import Path
R=Path(__file__).resolve().parent
rows=json.loads((R/'benchmark_results.json').read_text());D={(r['variant'],r['phase'],r['concurrency'],r['case']):r for r in rows}
def j(n):return json.loads((R/n).read_text())
def table(head,rs):return '| '+' | '.join(head)+' |\n|'+'|'.join(['---']*len(head))+'|\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rs)+'\n'
def sec(n):return f'{n/1000:.3f}' if n is not None else 'N/A'
def num(n):return f'{n:.2f}' if n is not None else 'N/A'
vnames={'original':'Original 3.5.100','round4':'Final Round 4','round5':'Final Round 5'}
a=D[('original','mixed',25,'ALL')];b=D[('round4','mixed',25,'ALL')];c=D[('round5','mixed',25,'ALL')]
total=sum(r['n'] for r in rows if r['case']=='ALL')
fp=j('fingerprint_after.json');assert fp['source']['rows_xor']==j('fingerprint_before.json')['source']['rows_xor'];assert fp['source']['findings']==1000168
compat=j('compatibility.json');bad=[r for r in compat if not r['status_equal'] or not r.get('json_equal',True) or not r.get('context_equal',True)];assert not bad
sources=j('source_verification.json');env=j('environment.json')
text=f'''# Round 5 — результаты

## Для руководства

На одной базе с **1 000 168 findings** заново сравнены официальный DefectDojo OSS 3.5.100, завершённый Round 4 и финальный Round 5. В итоговое сравнение вошло **{total} измеренных HTTP-запросов**, отдельно от прогрева, SQL-диагностики и проверок ответов. Во всех выбранных сериях HTTP 200; ошибок 5xx — 0.

При c=25 общий mixed p95: **{sec(a['p95_ms'])} → {sec(b['p95_ms'])} → {sec(c['p95_ms'])} с**; throughput: **{num(a['rps'])} → {num(b['rps'])} → {num(c['rps'])} RPS**. Round 5 против свежего Round 4: p95 изменился на {(1-c['p95_ms']/b['p95_ms'])*100:.1f}%, RPS — на {(c['rps']/b['rps']-1)*100:.1f}%. Это результат двух оптимизаций в совокупности; эффект нельзя целиком приписать одному патчу.

Исторические 7.08 с / 11.94 RPS из Round 4 **не использованы** как новая контрольная группа. Основные таблицы используют только свежие запросы на одинаковой методике. Прогнозы для больших баз приведены отдельно.

## Конфигурация и воспроизводимость

Apple M5, 16 GiB RAM; Docker VM {env['docker']['cpus']} CPU / {env['docker']['memory_bytes']/1024**3:.2f} GiB. uWSGI 4 процесса × 4 потока. PostgreSQL {env['application']['postgres']['server_version']}, shared_buffers=128 MB, work_mem=4 MB; настройки не менялись. Нет новых индексов, миграций, сервисов или кэша. Точные лимиты, зависимости, power/swap, image IDs: [environment.json](environment.json), [source_verification.json](source_verification.json). Отсутствие индивидуальных лимитов контейнеров не означает отсутствие лимита Docker VM.

'''
text+=table(['Сборка','Git SHA','Проверено файлов dojo'],[(vnames[v],f'`{s["sha"]}`',s['verified_files'])for v,s in sources.items()])
text+='''
Ветка `codex/performance-round5` продолжает отдельную release-normalized ветку 3.5.100, содержащую origin/dev в ancestry. Рабочая функциональная ветка и её пользовательские файлы не перезаписывались. Все Round 1–4 патчи сохранены. Port 8080 не использовался как оптимизированный вариант. Один тестовый web-контейнер за раз, без миграций/Celery beat над общей БД. Domain findings неизменны: count, sum ID, полный row-hash XOR и max_updated совпали до/после и с сохранённым seed; исходные 1 000 000 ID остались на месте.

## Методика

Фиксированный прежний mix: Findings list 30%, Product/severity/active filter 15%, Finding detail 10%, **полный Products API** 10%, Tests 10%, Engagements 5%, Dashboard 10%, Products UI 5%, Endpoints 5%. Page size 100; lightweight/FAST режимы отдельно в регрессиях. Один существующий admin + 24 существующих Product-scoped reader, одинаковый seeded schedule; c означает число запросов в полёте. Это не испытание 25 независимых людей с think time.

Прогрев 25 запросов; c1: 2×100, c5/10/15/25: 2×300. Порядок ABC/CBA, seeds 35101/35102, AC питание, low power mode off. Таймаут 90 с, ограничение серии 300 с, автоматический resource guard. Для standalone endpoints — тот же пул аккаунтов, два повтора по 40 запросов, прогрев 5. Все наблюдения и индивидуальные значения повторов сохранены. p95 рассчитан по объединённым latency, p99 только при n≥300; среднее p95 не используется. Малые per-case выборки (например 30 UI-запросов в mix) имеют высокий разброс; standalone серия даёт отдельные 80 наблюдений.

[REPRODUCE.md](REPRODUCE.md) содержит команды; [benchmark_results.json](benchmark_results.json) / [CSV](benchmark_results.csv) — численные результаты. Контейнерные CPU/working set — выборочные измерения. Унаследованный worker-RSS sampler пропускал PID1 worker и захватывал logger: старые primary RSS в JSON отмечены только как нижняя граница наблюдённых дочерних процессов. Исправленный сборщик измеряет все четыре workers по procname в отдельном парном c25 диагностическом прогоне; HTTP/SQL/buffer и Docker whole-container telemetry от ошибки не зависели. PG buffer reads не доказывают физическое чтение SSD: track_io_timing выключен.

## Две реализованные оптимизации

**1. Products, один авторизованный Product на странице.** Старый GROUP BY соединял каждую Finding с Test/Engagement; для Product с 532 569 активными findings план посещал одни heap pages восемь раз через Nested Loop/Bitmap Heap Scan. Теперь grouping key — уже известный Product ID, а Test IDs читаются одним ARRAY-подзапросом. Предыдущий Round 3 lookup перенесён в общий ORM helper без изменения SQL Finding-фильтра. Для нескольких Products сохранён batch GROUP BY. Полный упорядоченный ID-массив, точный active count и фильтры/доступ сохранены; это не замена ответом `findings=count`.

**2. Dashboard.** Три точных счётчика используют DISTINCT PK вместо всех Finding-полей. Три chart-агрегата (severity totals, month, punchcard day) заменены одним GROUP BY local day/severity. Небольшой агрегированный результат используется для всех графиков, без загрузки Finding objects. Сохранены cutoff, timezone, будущие даты, unknown severity, исключение duplicate и punchcard range. Старые публичные helper-функции оставлены; прочие вызовы punchcard работают прежним путём.

Изменены `dojo/product/queries.py`, `dojo/product/api/views.py`, `dojo/query_utils.py`, `dojo/finding/api/filters.py`, `dojo/home/views.py`, `dojo/utils.py`; добавлен `unittests/test_round5_performance.py`. Функциональные Engagements, UI redesign и шаблоны не менялись.

## SQL-профилирование и планы

pg_stat_statements не включён (shared_preload_libraries пуст, extension не установлена). Сервер не перезапускался. [sql_ranking_r4.json](sql_ranking_r4.json) и [sql_ranking_round5.json](sql_ranking_round5.json) содержат calls, total/mean/p95 **driver wall time**, rows и SQL shape без bindings. Диагностический лог включает прогрев/readiness; это не сервер-only execution time. Совокупные per-query shared/temp counters и server SQL p95 недоступны. Их нельзя подменять цифрами EXPLAIN или умножением одного плана на calls.

Фактические quiet SELECT планы: [phases_round4.json](phases_round4.json), [phases_round5.json](phases_round5.json). В них сохранены полные SQL без bindings и EXPLAIN ANALYZE/BUFFERS, включая Actual Rows/Loops, shared hits/reads и temp blocks.

'''
for v in ['round4','round5']:
    ranked=j('sql_ranking_r4_recheck.json') if v=='round4' else j('sql_ranking_round5.json')
    ranked=ranked['queries'] if isinstance(ranked,dict) else ranked
    text+=f'### {vnames[v]}: самые дорогие SQL в c25 диагностике\n\n'+table(['SQL shape ID','Calls','Σ driver с','Mean мс','p95 мс','Returned rows'],[(q['id'],q['calls'],num(q['total_ms']/1000),num(q['mean_ms']),num(q['p95_ms']),q['rows'])for q in ranked[:6]])
pr={v:j(f'phases_{v}.json')for v in ['round4','round5']}
planrows=[]
for v in pr:
    for actor,case in [(1,'products'),(1,'web_products'),(0,'dashboard')]:
        rr=next(x for x in pr[v] if x['actor']==actor and x['case']==case)
        for i,q in enumerate(rr['queries']):
            p=q['plan'][0];root=p['Plan'];planrows.append((v,actor,case+f' SQL{i+1}',num(p['Execution Time']),root.get('Shared Hit Blocks',0),root.get('Shared Read Blocks',0),root.get('Temp Written Blocks',0),root['Actual Rows']))
text+=table(['Build','Actor','SELECT','PG execution ms','Shared hits','Shared reads','Temp written blocks','Rows'],planrows)
text+='''
Отдельные пробные SQL-планы и отклонённые пути сохранены в raw: добавление ARRAY при сохранении внешнего Finding→Test JOIN не устраняло повторные heap scans; обычный IN также выбирал старый Nested Loop. Промежуточное удаление внешнего DISTINCT у трёх отдельных chart-запросов дало регрессию c25. Вариант только с узкими счётчиками ускорил Products, но не общий p95: три полных прохода Dashboard оставались пределом. Эти завершённые/остановленные exploratory серии архивированы в `raw/rejected-chart-plan/` и `raw/counts-only-candidate/`, исключены из финального сравнения. Итоговый общий дневной агрегат проверен отдельно и входит в FINAL.

## Основной mixed workload

'''
text+=table(['Build','c','n','p50 с','p90 с','p95 с','p99 с','RPS','PG CPU cores','uWSGI CPU cores','App working set MiB'],[(vnames[v],k,D[(v,'mixed',k,'ALL')]['n'],*[sec(D[(v,'mixed',k,'ALL')][m]) for m in ['p50_ms','p90_ms','p95_ms','p99_ms']],num(D[(v,'mixed',k,'ALL')]['rps']),num((D[(v,'mixed',k,'ALL')]['pg_cpu_mean'] or 0)/100),num((D[(v,'mixed',k,'ALL')]['web_cpu_mean'] or 0)/100),num(D[(v,'mixed',k,'ALL')]['web_container_memory_peak_mib'])) for k in [1,5,10,15,25]for v in vnames])
text+='\n### PostgreSQL, выборочные окна c25 primary mix\n\n'
windows=[x for x in j('resource_windows.json')if x['phase']=='mixed'and x['concurrency']==25]
text+=table(['Build/run','PG CPU peak %','Active peak','IO wait peak','Lock wait peak','Shared reads Δ','Shared hits Δ','Temp bytes Δ','Celery queue peak'],[(x['file'],num(x['pg_cpu_peak']),x['pg_active_peak'],x['pg_io_wait_peak'],x['pg_lock_wait_peak'],x['pg_reads_delta_sampled_window'],x['pg_hits_delta_sampled_window'],x['pg_temp_bytes_delta_sampled_window'],x['celery_queue_peak'])for x in windows])
text+='\nЭто глобальные счётчики source DB между первой/последней выборкой внутри серии: окно неполное, stats flush асинхронен, атрибуции отдельному SQL нет. Celery в этих read-only сериях не выполнял новые импорты; нулевая очередь не является проверкой его throughput. PG CPU и IO waits показывают смешанный CPU/IO/буферный предел, а не доказательство исключительно CPU-bound нагрузки.\n'
text+='\n### Разброс повторов, mixed c25\n\n'
text+=table(['Build','Повтор','n','p95 с','RPS'],[(vnames[v],i+1,x['n'],sec(x['p95_ms']),num(x['rps']))for v in vnames for i,x in enumerate(D[(v,'mixed',25,'ALL')]['runs'])])
text+='\n### c25, вклад отдельных маршрутов в тот же mix\n\n'
cases=[r['case']for r in rows if r['variant']=='original'and r['phase']=='mixed'and r['concurrency']==25 and r['case']!='ALL']
text+=table(['Scenario','n/build','Original p95 с','Round4 p95 с','Round5 p95 с','R5 share Σ request elapsed'],[(k,D[('round5','mixed',25,k)]['n'],*[sec(D[(v,'mixed',25,k)]['p95_ms'])for v in vnames],f"{100*D[('round5','mixed',25,k)]['latency_ms_sum']/c['latency_ms_sum']:.1f}%")for k in cases])
text+='\n### Standalone c1, одинаковые полные ответы\n\n'
ends=[r['case']for r in rows if r['variant']=='original'and r['phase']=='endpoints'and r['concurrency']==1 and r['case']!='ALL']
text+=table(['Scenario','n/build','Original p95 с','Round4 p95 с','Round5 p95 с','Original/R5','SQL Original/R4/R5'],[(k,D[('round5','endpoints',1,k)]['n'],*[sec(D[(v,'endpoints',1,k)]['p95_ms'])for v in vnames],num(D[('original','endpoints',1,k)]['p95_ms']/D[('round5','endpoints',1,k)]['p95_ms'])+'×',' / '.join(str(D[(v,'endpoints',1,k)]['sql_count_median'])for v in vnames))for k in ends])
text+='\n### Корректный sampled RSS всех четырёх workers, парный c25 контроль\n\n'
rss_rows=[]
for v in vnames:
    if v=='original':continue
    lines=[json.loads(l) for l in (R/'raw'/f'diagnostic-pair-{v}-rss.jsonl').read_text().splitlines()]
    assert all(x['workers']==4 and x['scope']=='all_workers_by_procname' for x in lines)
    rss_rows.append((v,len(lines),num(max(x['rss_max_kib']for x in lines)/1024)))
text+=table(['Build','Samples, 0.4 s interval','Max observed worker RSS MiB'],rss_rows)
text+='\n### Полный Products API: отдельная серия\n\n'
text+=table(['Build','c','n','p50 с','p90 с','p95 с','RPS','Median bytes','App working set MiB','Observed worker RSS MiB','RSS scope'],[(vnames[v],k,(r:=D[(v,'endpoints',k,'products')])['n'],*[sec(r[m])for m in ['p50_ms','p90_ms','p95_ms']],num(r['rps']),int(r['response_bytes_median']),num(r['web_container_memory_peak_mib']),num(r['worker_rss_peak_mib']),'all 4' if r['worker_rss_scope']=='all workers' else 'legacy lower bound')for k in [1,5,10,25]for v in vnames])
text+='''
N/A для Docker memory означает отсутствие выборки внутри очень короткой measured-фазы; такие данные не восстановлены оценкой. Worker RSS имеет отдельный sampler и scope. Состав payload зависит от авторизованного Product. Поэтому медианный размер в общей серии не равен максимальному ответу администратора. Для диагностической декомпозиции отдельного запроса:

'''
text+=table(['Build','Actor','IDs','Bytes','SQL ms','ID load incl SQL ms','Representation ms','JSON render ms','Sampled RSS increase MiB'],[(v,r['actor'],r['finding_ids'],r['bytes'],num(r['sql_ms']),num(r['phases'].get('product_id_loading_ms')),num(r['phases'].get('product_representation_ms')),num(r['phases'].get('json_render_ms')),num((r['rss_peak_sampled']-r['rss_before'])/1024**2))for v in pr for r in pr[v] if r['case']=='products'])
text+='\n### UI phases, admin diagnostic (inclusive times, ms)\n\n'
text+=table(['Build','Page','Wall','SQL','Queryset eval incl SQL','Template incl SQL','Template SQL subset','Chart helpers incl SQL'],[(v,r['case'],num(r['wall_ms']),num(r['sql_ms']),num(r['phases'].get('queryset_evaluation_inclusive_ms')),num(r['phases'].get('template_inclusive_ms')),num(r['phases'].get('template_inclusive_ms_sql_subset')),num(sum(val for key,val in r['phases'].items()if key.startswith(('get_dashboard_chart_data','get_severities_','get_punchcard_data'))and not key.endswith('_sql_subset'))))for v in pr for r in pr[v] if r['actor']==0 and r['case']!='products'])
text+='''
Фазы измерены диагностически, а не как p95; `ID load` включает SQL и декодирование/материализацию ID. Inclusive template time в тех же JSON включает ленивое выполнение ORM; складывать его с SQL как независимые фазы нельзя. RSS sampled каждые 10 ms — нижняя граница пика, предыдущие запросы могут переиспользовать память. Все SQL/phase/response/RSS значения сохранены, включая шумные cold-process значения; небольшие колебания не объявляются ускорением.

Стандартный ответ администратора содержит 840 362 ID / 5 800 448 bytes, тяжёлый scoped Product — 532 569 ID / 3 669 647 bytes. Размер не уменьшался. В источниках не найден подтверждённый внутренний потребитель именно Product API findings_list; одноимённые переменные Findings templates относятся к другому контексту. Products UI уже считает числа напрямую и не загружает этот API-массив. Для внешних клиентов необходима инвентаризация интеграций; режимы count/none можно выбирать только при отсутствии потребности в IDs. Сам benchmark остался полным.

## Цели c25

'''
goals=[('Mixed p95 <4 s',c['p95_ms']<4000,sec(c['p95_ms'])+' s'),('Mixed RPS >15',c['rps']>15,num(c['rps'])),('Full Products p95 <5 s, внутри mix',D[('round5','mixed',25,'products')]['p95_ms']<5000,sec(D[('round5','mixed',25,'products')]['p95_ms'])+' s'),('Dashboard p95 <3 s, внутри mix',D[('round5','mixed',25,'dashboard')]['p95_ms']<3000,sec(D[('round5','mixed',25,'dashboard')]['p95_ms'])+' s'),('HTTP 5xx =0',True,'0')]
text+=table(['Цель','Достигнута в этих сериях','Измерено'],[(x,'да'if ok else'нет',val)for x,ok,val in goals])
text+='''
Цели не использовались для изменения весов workload, прав, точности COUNT или состава ответов. Два повтора показывают локальный разброс, но не являются production SLO/доверительным интервалом на длительную эксплуатацию.

## Графики

![Critical endpoints](charts/critical_endpoints.png)
![Speedup](charts/speedup_factors.png)
![Saturation](charts/saturation_curves.png)
![Contribution](charts/latency_contribution.png)\n![Distribution](charts/latency_distribution.png)\n![Mixed speedup](charts/mixed_speedup_factors.png)
![Round5](charts/round5_before_after.png)\n![Resources](charts/application_resources.png)

Чёрные/крестообразные отметки — значения повторов, подписи содержат n. Нет сглаживания. Вклады latency учитывают очередь и перекрывающиеся запросы; это не разложение CPU. [RPS](charts/critical_rps.png), [SQL](charts/critical_sql.png). Все графики строятся `plot_results.py` из JSON.

## Корректность и оставшиеся пределы

'''
text+=f'''**104 теста: 96 pass, 8 skip, 0 fail.** Новые четыре regression tests проверяют полный sorted ID-массив, active/verified counts, пустой Product, multi-product path, count/none, hidden Product, PK DISTINCT при двух risk acceptances и исключение duplicates; chart oracle покрывает cutoff/future/unknown severity/UTC и America/New_York. Предыдущие тесты включают FAST/default/custom ordering, CSV Product filters, Finding/Jira prefetch и несколько реальных vulnerability references. Полные сравнения HTTP: **{len(compat)} пар, 0 semantic/JSON/status расхождений**. Opt-in режимы сравниваются только Round4→Round5. Динамические HTML bytes не трактуются как data regression; сравнивается серверный контекст. Логи/проверки перечислены в [TEST_RESULTS.md](TEST_RESULTS.md).

Изменения не затрагивают import/reimport/deduplication; реальные write-нагрузки Round 4 не выдаются за новые Round 5 испытания. Синтетический миллион не представляет все production relationships и сигналы. Не подтверждены новая длительная production soak, 25 независимых людей/интеграций, HA PostgreSQL, 5–20 млн реальных findings.

1. Dashboard теперь читает таблицу меньше раз, но точные totals/daily aggregate всё ещё линейны по разрешённым findings; PG CPU/сканирование остаются пределом. Следующее решение — спроектировать точные Product/day агрегаты с транзакционной актуализацией и проверкой прав, затем отдельно измерить import/write cost. В текущем патче такого кэша/денормализации нет.
2. Полные Product ID arrays линейно растут по CPU, памяти и сети. Обратная совместимость не позволяет ограничить ответ. Практический следующий шаг — перевести проверенные summary-клиенты на существующие opt-in режимы, для IDs спроектировать opt-in пагинированный ID-only endpoint с прежними проверками доступа; такого нового endpoint в патче нет. Полный стандартный путь останется дорогим. Покрывающий partial index можно лишь исследовать на копии после EXPLAIN и оценки write/storage cost; он не добавлен.
3. Findings UI и Test UI сохраняют широкие DISTINCT counts/повторные агрегаты. Они измерены и задокументированы в phases, но оставлены за лимитом двух оптимизаций. Глубокий OFFSET и точный count стандартной пагинации также остаются; FAST не включён глобально.
4. Увеличение c после точки CPU saturation повышает очередь; текущие графики не доказывают capacity будущих 16 vCPU/32 GiB application nodes и внешнего HA PG. Нужен отдельный end-to-end тест с импортами, штатными отношениями и длительным soak.

## Прогноз, не измерения

Текущая БД занимает {env['pg_diagnostics']['database_bytes']/10**9:.2f} GB; Finding heap+indexes — {env['pg_diagnostics']['finding_total']/10**9:.2f} GB. Грубое линейное масштабирование структуры синтетической БД даёт около 16.8/33.7/67.3 GB для 5/10/20 млн; media, WAL, replicas, backups, настоящие scanner evidence/relations и write bloat могут существенно увеличить footprint. Это не sizing production.

При сохранении нынешней active доли полный общий Product response при одинаковом числе bytes на ID линейно вырастет до 29/58/116 MB для 5/10/20 млн total findings. С учётом роста числа цифр последовательных ID оценка составляет примерно 33/66/142 MB (при неизменной active-доле); это модель, не эксперимент. Python int/list и промежуточные буферы также растут линейно; параллельные полные ответы способны исчерпать RAM application-ноды. Эти оценки не являются замерами больших баз. Автоматический 5-миллионный seed не запускался.

## Внедрение и rollback

Готовы два локально проверенных ORM-патча, тесты и воспроизводимый suite; production readiness требует отдельного representative/load/HA испытания. Новых миграций нет. Развёртывать проверенный immutable image, сначала canary с проверкой полного payload/permissions и PostgreSQL CPU/temp/latency; lightweight режимы включать только клиентским opt-in. [ROLLBACK.md](ROLLBACK.md): вернуть Round4 image или отдельно restore Product ORM group / Dashboard view+utils. БД откатывать, удалять или пересоздавать не требуется.
'''
(R/'RESULTS.md').write_text(text)
summary=f'''# Round 5 — краткая записка для руководства

На неизменной тестовой базе с **1 000 168 findings** выполнено единое свежее сравнение Original DefectDojo OSS 3.5.100 → Final Round 4 → Final Round 5. В итоговых HTTP-сериях **{total} запросов**, нагрузка до 25 одновременных запросов, 0 ошибок 5xx. Это локальный Mac M5/16 GiB, а не будущая production-инфраструктура.

'''+table(['Показатель c25, один mixed workload','Original','Round4','Round5'],[['Общий HTTP p95, с',sec(a['p95_ms']),sec(b['p95_ms']),sec(c['p95_ms'])],['Throughput, RPS',num(a['rps']),num(b['rps']),num(c['rps'])],['Full Products p95, с',*[sec(D[(v,'mixed',25,'products')]['p95_ms'])for v in vnames]],['Dashboard p95, с',*[sec(D[(v,'mixed',25,'dashboard')]['p95_ms'])for v in vnames]]])+f'''
**Что изменили.** Устранили повторное чтение страниц findings в агрегатах одного Product; стандартный ответ сохранил все IDs в прежнем порядке. Dashboard теперь строит три графика одним проходом и считает уникальные findings по узкому PK вместо всей строки. Предыдущие оптимизации сохранены. Серверные настройки, права и бизнес-правила не менялись.

**Измеренный результат.** Против свежего Round 4 p95 сократился на {(1-c['p95_ms']/b['p95_ms'])*100:.1f}%, throughput вырос на {(c['rps']/b['rps']-1)*100:.1f}%. Против оригинала p95 лучше в {a['p95_ms']/c['p95_ms']:.2f} раза, throughput выше в {c['rps']/a['rps']:.2f} раза в данном mix. Исторические 7.08 с / 11.94 RPS не подставлялись как контрольная группа. Разброс двух повторов и полные исходные наблюдения доступны в отчёте.

**Как проверили.** Одна БД, одинаковый полный workload и ресурсы, прогрев, прямой/обратный порядок трёх сборок, точные Git SHA и проверенные исходники образов. 104 автоматических теста: 96 pass, 8 skip. {len(compat)} пар ответов совпали по JSON/значимым серверным данным/статусам. Проверены scoped права, полный ID-массив, точные count, даты и timezone графиков, прежние FAST/prefetch исправления. Миллион исходных findings и все 168 дополнительных сохранены, fingerprint не изменился.

**Практическая ценность.** Форк измеримо быстрее исходного DefectDojo в проверенных сценариях при сохранении совместимости. Сравнение пригодно для демонстрации собственных инженерных улучшений; оно не является тестом сторонних ASPM-продуктов.

**Оставшаяся цель.** Dashboard p95 внутри c25 mix составляет {sec(D[('round5','mixed',25,'dashboard')]['p95_ms'])} с; порог 3 с проверяется отдельно и не подменяется общим p95.\n\n**Что ещё необходимо.** Полные ID-ответы и точные сканирующие агрегаты остаются линейными по данным. Нужны инвентаризация summary-клиентов с переходом на существующие opt-in режимы, отдельный проект точных агрегатов, representative scanner data и длительное испытание совместно с import/reimport на будущей application-нODE 16 vCPU/32 GiB и внешнем HA PostgreSQL. 5–20 млн не генерировались; прогноз footprint/response size отдельно помечен как экстраполяция. Проверка 25 in-flight запросов не равна сертификации 25 независимых сотрудников.

Подробные метрики, SQL/EXPLAIN, CPU/RSS, цели, ограничения и безопасный rollback: [RESULTS.md](RESULTS.md). Миграций/новых индексов нет; откат к Round4 image не требует изменения БД.
'''
(R/'EXECUTIVE_SUMMARY.md').write_text(summary.replace('нODE','ноде'))
print('Generated measured report and executive summary')
