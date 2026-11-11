#!/usr/bin/env python3
"""Generate filled reports from selected, completed experiments."""
import json
import math
import statistics
from pathlib import Path

R=Path(__file__).resolve().parent
D=json.loads((R/'benchmark_results.json').read_text())
E=json.loads((R/'environment.json').read_text())
C=json.loads((R/'runtime_configuration.json').read_text())
F=json.loads((R/'fingerprint_final.json').read_text())['source']
CHECKS=json.loads((R/'final_checks.json').read_text())['resource_guard']
B=json.loads((R/'background_correctness.json').read_text())
assert B['api_statistics_equal']
rows=D['summary']
assert D['failed_requests']==0


def metric(phase,variant,case='mixed',c=25):
    return next(r for r in rows if (r['phase'],r['variant'],r['case'],r['concurrency'])==(phase,variant,case,c))


def number(x,d=1):
    return '—' if x is None else f'{x:,.{d}f}'.replace(',',' ')


def pct(a,b):return 100*(b/a-1)


def p95(samples):
    x=sorted(s['ms'] for s in samples if s['status']=='200')
    return x[math.ceil(.95*len(x))-1] if len(x)>=20 else None


original=metric('mixed','original');current=metric('mixed','current');final=metric('mixed','final')
primary=sum(r['requests'] for r in rows if r['phase'] in ('endpoints','mixed','users'))
bg=sum(r['requests'] for r in rows if r['phase'].startswith('background-'))
compat=json.loads((R/'compatibility.json').read_text())
json_pairs=sum('json_equal' in r for r in compat)
html_pairs=sum('context_equal' in r for r in compat)
labels={'findings':'Findings list, 100','finding_detail':'Finding detail','filtered_product':'Findings, Product + High + active','filtered_severity':'Findings, High + active','offset':'Findings, OFFSET 500000','products':'Products full list','product_detail':'Product full detail','engagements':'Engagements list','engagement_detail':'Engagement detail','tests':'Tests list','test_detail':'Test detail','product_types':'Product types','users':'Users','endpoints':'Endpoints','endpoint_status':'Endpoint status','notes':'Notes','dashboard':'Dashboard','web_products':'Products UI','web_findings':'Findings UI','web_engagements':'Engagements UI','web_test':'Test UI','simple_metrics':'Simple Metrics, cache hit','simple_metrics_cold':'Simple Metrics, fresh render'}
endpoint_table=[]
for case,label in labels.items():
    a=metric('endpoints','original',case,1);b=metric('endpoints','final',case,1)
    endpoint_table.append(f"| {label} | {number(a['p95_ms'])} | {number(b['p95_ms'])} | {a['p95_ms']/b['p95_ms']:.2f}× | {number(a['sql_count_median'],0)} | {number(b['sql_count_median'],0)} |")
mixed_table=[]
resource_table=[]
for c in (1,5,10,15,25):
    triplet=[metric('mixed',v,c=c) for v in ('original','current','final')]
    mixed_table.append('| '+str(c)+' | '+' | '.join(f"{number(x['p50_ms'])} / {number(x['p95_ms'])} / {number(x['p99_ms'])}; {number(x['rps'],2)}" for x in triplet)+' |')
    for x in triplet:
        resource_table.append(f"| {c} | {x['variant']} | {number(x['uwsgi_cpu_peak'],0)} | {number(x['pg_cpu_peak'],0)} | {number(x['uwsgi_worker_rss_mib_peak'],0)} | {number(x['pg_container_mib_peak'],0)} | {x['pg_connections_peak']} | {number(x['pg_reads_sampled_delta'],0)} | {number(x['pg_temp_bytes_sampled_delta']/1024**2 if x['pg_temp_bytes_sampled_delta'] is not None else None,1)} |")
users_table=[]
for v in ('original','current','final'):
    x=metric('users',v)
    users_table.append(f"| {v} | {x['observed_users']} | {x['requests']} | {number(x['p95_ms'])} | {number(x['rps'],2)} | 0% |")
opt_table=[]
for case in ('products_count','products_none','fast_offset'):
    for v in ('current','final'):
        x=metric('endpoints',v,case,1)
        opt_table.append(f"| {case} | {v} | {number(x['p95_ms'])} | {number(x['rps'],2)} | {number(x['response_bytes_median'],0)} | {number(x['sql_count_median'],0)} |")
imports={}
import_table=[]
read_impact=[]
task_summary={}
for v in ('original','current','final'):
    imports[v]={phase:json.loads((R/'raw'/f'import-{v}-{phase}.json').read_text()) for phase in ('idle','loaded')}
    for op in ('import','reimport','duplicates'):
        med={phase:statistics.median((r['end']-r['start'])*1000 for r in imports[v][phase] if r['operation']==op) for phase in ('idle','loaded')}
        import_table.append(f"| {v} | {op} | {number(med['idle'])} | {number(med['loaded'])} | 3 + 3 |")
    a=metric('background-control',v,c=10);b=metric('background-loaded',v,c=10)
    read_impact.append(f"| {v} | {number(a['p95_ms'])} | {number(b['p95_ms'])} | {number(a['rps'],2)} | {number(b['rps'],2)} | 600 + 600 |")
    events=json.loads((R/f'celery_{v}.json').read_text())
    tasks=[r for r in events if r['event']=='finished']
    assert tasks and all(t['state']=='SUCCESS' for t in tasks)
    delays=[(r['at']-r['published_at'])*1000 for r in events if r['event']=='received' and r.get('published_at') is not None]
    task_summary[v]={'tasks':len(tasks),'sql_total':sum(t['sql_count'] for t in tasks),'sql_ms_total':sum(t['sql_ms'] for t in tasks),'task_runtime_ms_total':sum(t['duration_ms'] for t in tasks),'worker_hwm_mib':max(t['rss_hwm_kib'] for t in tasks)/1024,'delivery_p50_ms':statistics.median(delays) if delays else None,'delivery_p95_ms':sorted(delays)[math.ceil(.95*len(delays))-1] if len(delays)>=20 else None}
(R/'background_summary.json').write_text(json.dumps(task_summary,indent=2)+'\n')
task_table=['| '+v+' | '+str(t['tasks'])+' | '+number(t['sql_total'],0)+' | '+number(t['sql_ms_total'])+' | '+number(t['worker_hwm_mib'])+' | '+number(t['delivery_p95_ms'])+' |' for v,t in task_summary.items()]
case_table=[]
for case in ('findings','filtered_product','finding_detail','products','dashboard','web_products'):
    selected=[next(r for r in D['mixed_by_case'] if r['phase']=='mixed' and r['variant']==v and r['concurrency']==25 and r['case']==case) for v in ('original','current','final')]
    case_table.append('| '+case+' | '+' | '.join(number(r['p95_ms'])+f" (n={r['requests']})" for r in selected)+' |')
new_effects=[]
for case in ('web_products','dashboard','simple_metrics_cold'):
    a=metric('endpoints','current',case,1);b=metric('endpoints','final',case,1)
    new_effects.append(f"| {labels[case]} | {number(a['p95_ms'])} → {number(b['p95_ms'])} мс | {a['p95_ms']/b['p95_ms']:.2f}× | {number(a['sql_count_median'],0)} → {number(b['sql_count_median'],0)} | {number(a['uwsgi_worker_rss_mib_peak'],0)} → {number(b['uwsgi_worker_rss_mib_peak'],0)} МиБ |")
footprint=F['database_bytes']/1e9
scale='\n'.join(f'| {n} млн | {footprint*(n*1000000/F["findings"]):.1f} | {footprint*(n*1000000/F["findings"])*1.7:.0f}–{footprint*(n*1000000/F["findings"])*2:.0f} |' for n in (5,10,20))
report=f'''# DefectDojo 3.5.100 — Final Performance Report

## A. Executive Summary

На одном локальном стенде и неизменных **{F['findings']:,} findings** выполнено **{primary:,} измеренных read-only запросов**. Дополнительно выполнены {bg:,} запросов чтения и 54 import/reimport POST на трёх одинаковых копиях с корректной статистикой PostgreSQL. В выбранных итоговых сериях HTTP error rate — **0%**.

В mixed workload при 25 одновременно выполняемых запросах Original → Final: **p95 {original['p95_ms']/1000:.2f} → {final['p95_ms']/1000:.2f} с**, **RPS {original['rps']:.2f} → {final['rps']:.2f}**. Throughput вырос на **{pct(original['rps'],final['rps']):.1f}%**, p95 снизился на **{-pct(original['p95_ms'],final['p95_ms']):.1f}%**. От CURRENT с Round 1–3 до FINAL: RPS **{current['rps']:.2f} → {final['rps']:.2f}**, p95 **{current['p95_ms']/1000:.2f} → {final['p95_ms']/1000:.2f} с**.

Это стресс-тест полных стандартных API-ответов, Dashboard и Products UI. Он не сопоставим с прежними 39,1 RPS, полученными на другом mix с Product `findings=count`. Система ещё имеет многосекундные хвосты; готовность к 20 млн findings и production SLA здесь не доказана.

### Стенд и происхождение сборок

- ORIGINAL: официальный tag `3.5.100`, commit `334bef02d65a74909fe976b22724526474d5a0f6`; SHA сверён через upstream `git ls-remote`.
- CURRENT: `20771ddc0bdfb4b763708f70e1cd6c131c3f6b5e` — все фактические runtime-патчи Round 1–3 интегрированы в Git.
- FINAL: `70daa20757a9b5b99836343e50791a4de8c72fd0` — три новых исправления.
- Предыдущий `ea9f153a36` не содержал всех Finding runtime-файлов. Интеграция восстановила их и нормализовала семь несвязанных dev-файлов до релиза. [Манифест](integration_manifest.json).
- Код `/app/dojo` ORIGINAL полностью взят из чистого тега. Для CURRENT/FINAL проверены Git blob hashes и файлы в образах. Остальные runtime-зависимости, entrypoints и статические артефакты — из одного зафиксированного родительского образа. Непроверенная сборка на 8080 не использовалась как FINAL.
- Apple M5, 16 ГиБ RAM; Docker/OrbStack {E['docker']['cpus']} CPU и {E['docker']['memory_bytes']/1024**3:.3f} ГиБ RAM. PostgreSQL {C['postgres']['server_version']}, Django {C['django']}, DRF {C['drf']}, Python {C['python']}. uWSGI 4 процесса × 4 потока, `CONN_MAX_AGE=0`. PG `shared_buffers={C['postgres']['shared_buffers']}`, `work_mem={C['postgres']['work_mem']}`, `max_connections={C['postgres']['max_connections']}`. Отдельные cgroup CPU/RAM limits отсутствуют.
- Один активный benchmark web-container; старые Round 1–3 benchmark web-контейнеры временно остановлены. Основной 8080 и его данные сохранены. Изменений глобальной конфигурации PostgreSQL/Docker нет.

[Окружение и image IDs](environment.json) · [Runtime config](runtime_configuration.json) · [Проверка официального тега](official_tag_verification.txt) · [Fingerprint до/после чтения](fingerprint_after_readonly.json)

## B. Оптимизации по этапам

Исторические цифры ниже относятся к своим исходным испытаниям и не перемножаются в кумулятивное ускорение. Эти ранее выполненные исправления сохранены, их эффект заново проверяется в общей матрице C/D.

| Этап | Компонент | Проблема | Исправление | Ранее измеренный эффект |
|---|---|---|---|---|
| Round 1 | Finding API | N+1 vulnerability references | Prefetch в обеих ветках | 123 → 24 SQL на 100 findings |
| Round 1 | Pagination | Глубокий OFFSET | Opt-in two-stage ID pagination | OFFSET 500000, c=1: p95 640,74 → 291,68 мс |
| Product | Product API | Повторные COUNT и ID-запросы | Batch ordered IDs | c=1: SQL 22 → 10; p95 6170,7 → 1217,6 мс |
| Round 2 | Product detail/summary | Загрузка ID ради count | Detail batch; `findings=count/none` | Меньше загрузка ID и память; облегчённый ответ — отдельный контракт |
| Round 2 | Test Jira | N+1 связанных групп | Prefetch Jira relations | Fixture со 100 Tests: SQL 408 → 12 |
| Round 3 | Finding Product filter | Повторные heap scans в COUNT | Test IDs initplan + ANY array | Старый mix c=25: p95 2,23 → 1,19 с; RPS 32,6 → 39,1 |
| Round 4 | Products UI | Три коррелированных finding count на Product | Один групповой агрегат для страницы | Свежие CURRENT → FINAL ниже |
| Round 4 | Dashboard | Двойная дневная агрегация и два EXTRACT | Одна загрузка дневных групп; TruncMonth | Свежие CURRENT → FINAL ниже |
| Round 4 | Simple Metrics | Полные Finding-объекты ради чисел | SQL aggregation и узкий exact count | Свежие CURRENT → FINAL ниже |

Источники исторических результатов: [Round 1/Product](../RESULTS.md), [Round 2](../ROUND2_RESULTS.md), [Round 3](../ROUND3_RESULTS.md).

## C. ORIGINAL → FINAL: единая матрица

Одинаковые URL, права, БД и page size, concurrency 1. По 2 × 40 измеренных запросов, по 5 warmup на серию. SQL — медиана фактически измеренных statements на HTTP-запрос. p95 ниже в миллисекундах. Малые изменения контрольных маршрутов не считаются доказанным выигрышем.

| Endpoint / Scenario | Original p95 | Final p95 | Speedup (observed) | Original SQL | Final SQL |
|---|---:|---:|---:|---:|---:|
{chr(10).join(endpoint_table)}

Стандартный Products full имеет прежние данные и полный список ID; его размер не уменьшался. Полные RPS, p50/p99, размеры ответов, SQL milliseconds и RSS сохранены в [CSV](benchmark_results.csv) и [JSON](benchmark_results.json). p99 для endpoint n=80 не рассчитывается.

### Новые изменения: CURRENT → FINAL

| Сценарий | p95 | Ratio | SQL statements | Пик RSS worker в серии |
|---|---:|---:|---:|---:|
{chr(10).join(new_effects)}

RSS — выборочные значения работающих процессов и включает память, оставшуюся от предыдущих сценариев. Это не изолированный прирост памяти одного запроса. SQL count Products UI вырос на один, при этом исчезли дорогие повторные вычисления. [Причины, SQL и EXPLAIN](NEW_BOTTLENECKS.md).

### Opt-in режимы

Эти ответы не сравниваются с полным ORIGINAL как одинаковая нагрузка. FAST остаётся экспериментальным; глобально не включён.

| Сценарий | Build | p95, мс | RPS | Response bytes | SQL |
|---|---|---:|---:|---:|---:|
{chr(10).join(opt_table)}

## D. Общая производительность системы

Фиксированный mix: 30% Findings list, 15% Findings Product/High/active, 10% finding detail, 10% Products full, 10% Tests, 5% Engagements, 10% Dashboard, 5% Products UI, 5% Endpoints. Основной тест — saturation, без think time; использованы один superuser и 24 аккаунта с Product membership. 25 идентичностей распределены по воспроизводимому расписанию независимо от concurrency.

При c=1 — 2 × 100 запросов на вариант; при c=5/10/15/25 — 2 × 300. По 25 warmup. Первый раунд ORIGINAL → CURRENT → FINAL, второй FINAL → CURRENT → ORIGINAL. p95 и p99 рассчитаны по объединённым request samples, а не усреднением квантилей. RPS = все запросы / сумма длительностей измеренных серий. Для c=1 n=200, p99 не публикуется; при n=600 p99 остаётся оценкой небольшого числа хвостовых наблюдений.

| Concurrency | ORIGINAL p50/p95/p99, мс; RPS | CURRENT p50/p95/p99, мс; RPS | FINAL p50/p95/p99, мс; RPS |
|---:|---:|---:|---:|
{chr(10).join(mixed_table)}

### Критические сценарии внутри mix, c=25

| Case | ORIGINAL p95, мс | CURRENT p95, мс | FINAL p95, мс |
|---|---:|---:|---:|
{chr(10).join(case_table)}

Throughput выходит на плато около c=10–15, затем растёт задержка. uWSGI имеет 16 execution slots; при c=25 вероятно ожидание свободного слота. Его точная очередь отдельно не инструментировалась. В этом mix PostgreSQL CPU — ведущий предел: на c=25 PostgreSQL занимает около восьми логических ядер, uWSGI — примерно полтора-два. Дорогие exact counts и полные ID-массивы остаются ограничениями; Python-материализация особенно существенна для формирования Simple Metrics. Увеличение processes/threads в этом раунде не применялось.

### Независимые пользователи

Отдельная модель: 25 фиксированных аккаунтов, каждый выполняет свою заранее назначенную последовательность, think time 0,25 с. Это закрытая ограниченная серия, не моделирование неизвестного production arrival rate. Её числа не смешиваются с saturation.

| Build | Users | Requests | p95, мс | RPS | Errors |
|---|---:|---:|---:|---:|---:|
{chr(10).join(users_table)}

### Ресурсы mixed workload

Пики выборочного опроса; 100% CPU = одно логическое ядро. PG memory — память контейнера, не сумма RSS процессов. Deltas buffer reads/temp — сумма наблюдаемых изменений внутри серий, с несэмплированными краями; они включают фоновую активность и не означают физические чтения SSD. `track_io_timing=off`, точное время дискового I/O недоступно.

| c | Build | uWSGI CPU % | PG CPU % | Worker RSS MiB | PG container MiB | PG connections | Sampled shared reads | Sampled temp MiB |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(resource_table)}

Сторож контролировал OOM, состояние контейнеров, суммарную память Docker, host memory pressure, swap и AC/Low Power Mode. Наращивание нагрузки разрешалось только после успешных предыдущих уровней. Свободная память хоста в сэмплах оставалась не ниже {CHECKS['min_host_free_percent']}%; swap {CHECKS['min_swap_mib']:.0f}–{CHECKS['max_swap_mib']:.0f} МиБ. Срабатываний guard не было. Подробные временные ряды находятся в `raw/*-metrics.jsonl` и `raw/*-rss.jsonl`.

## E. Графики

Автоматически построены из JSON/CSV скриптом [plot_results.py](plot_results.py), зависимости зафиксированы в [chart-requirements.txt](chart-requirements.txt).

![Endpoint p95](charts/endpoint_p95.png)
![Endpoint RPS](charts/endpoint_rps.png)
![SQL count](charts/sql_queries.png)
![Mixed p95](charts/mixed_p95.png)
![Mixed RPS](charts/mixed_rps.png)
![CPU и память](charts/resources.png)

## F. Корректность и background processing

**100 тестов: 92 passed, 8 skipped**. Новые regression guards воспроизвели четыре падения на CURRENT до исправлений; FINAL прошёл их. Все тесты повторены с файлами непосредственно из Git worktree, включая восстановленный модуль проверок прежнего runtime.

Сравнены {json_pairs} полных JSON payload-пары и {html_pairs} HTML context-пары: ошибок нет. Дополнительно проверены сортировка, count, страницы, доступ к чужим данным, CSV-фильтры, ordered vulnerability references с двумя связанными ID, FAST и fallback при нестандартной сортировке. HTML не объявляется побайтно идентичным: динамические значения дают различия хэшей; шаблоны не менялись. [Подробности](TEST_RESULTS.md), [пары ответов](compatibility.json).

### Import/reimport и дедупликация

Контролируемые ZAP scans: 40 alerts, по три URL с request/response evidence. В каждом варианте 3 последовательности без нагрузки и 3 под чтением c=10: import → reimport с заменой четырёх правил → duplicate-peer import. Продукт до теста имел 633794 findings; дедупликация выполнялась по Product. Использован поддерживаемый API и `async_wait`, один Celery worker process с hard limit 120 с. Каждый вариант начинал с идентичной копии 1000168 findings, той же статистикой планировщика и отдельными broker DB/media. Первые копии без column statistics исключены и сохранены в [архиве диагностики](background_unanalyzed/planner_statistics.json). Каноническая копия прошла ANALYZE перед созданием окончательных копий. Исходная БД не менялась.

Все 54 POST вернули 201 и завершённую дедупликацию. В каждой последовательности primary Test содержит 44 findings, из них 40 active; peer Test содержит 40 findings и 40 duplicates. Evidence и Location references присутствуют. API statistics совпали во всех трёх вариантах. [Прямые проверки БД](background_correctness.json).

| Build | Операция | Median idle, мс | Median under c=10, мс | Samples |
|---|---|---:|---:|---:|
{chr(10).join(import_table)}

| Build | Read control p95 | Read + imports p95 | Control RPS | Loaded RPS | Requests |
|---|---:|---:|---:|---:|---:|
{chr(10).join(read_impact)}

У каждого варианта одна control/loaded пара чтения; её нельзя считать надёжной оценкой причинного влияния импорта на production p95. Между сериями добавляются несколько сотен findings и прогревается кеш. Импортная производительность не заявляется отдельной успешной оптимизацией Round 4: импортный код не менялся.

| Build | Celery tasks SUCCESS | Task SQL executions | Task SQL total, мс | Worker HWM MiB | Publish→receive p95, мс |
|---|---:|---:|---:|---:|---:|
{chr(10).join(task_table)}

Время/SQL task измерены между Celery prerun/postrun, HWM накопительный для worker process. Publish/receive timestamps добавлены одинаковой benchmark-only инструментализацией; аргументы задач и SQL params не записывались. Подробности: [background summary](background_summary.json), `celery_*.json`, `raw/import-*.json`.

## G. Остаточные bottleneck

1. Exact COUNT Findings и ограниченных пользовательских scopes: работа растёт с подходящими строками. Отдельно остаются широкие DISTINCT-проекции Dashboard counters и заметные temp spills; это следующая задача для проверки узкого count по PK, а не повод удалять точный count.
2. Полный Products API читает и сериализует все активные ID: объём не ограничен числом Products на странице. Нужны осознанное использование существующих opt-in режимов и отдельная загрузка findings.
3. Standard deep OFFSET проходит строки до смещения. FAST ограничен подходящей сортировкой и остаётся opt-in.
4. PostgreSQL CPU/буферные чтения и Python CPU: RPS уже выходит на плато; простое увеличение клиентов увеличивает очередь и p95.
5. Findings UI и Test UI остаются дорогими; новые патчи их серверные запросы не оптимизируют.
6. Simple Metrics теперь ограничивает материализацию, но exact aggregates по большим Product Types всё ещё дороги, а число запросов зависит от числа типов.
7. В Notes API обнаружена загрузка history по строкам; на этом маленьком наборе абсолютная стоимость мала, поэтому патч не выбран.
8. Реальные импорты с историческими совпадениями, разными сканерами, большими evidence и одновременными интеграциями требуют отдельного объёмного теста.

## H. Масштабирование

Измерено только около 1 млн findings. Основная БД занимает {footprint:.2f} GB. Ниже — линейная экстраполяция разреженного синтетического storage footprint, а не измерение на 5–20 млн и не бюджет production. Disk reserve 1,7–2× условно учитывает рабочее место/WAL/bloat, резервные копии отдельно.

| Findings | Данные + индексы, GB | Рабочий диск, GB |
|---|---:|---:|
{scale}

Многие синтетические строки не имеют production-плотности CWE, references, Locations, evidence, history и импортных связей. Реальная база может быть существенно больше. Полные ID-ответы растут линейно и способны занять сотни MB на ответ. Нагрузка 25 клиентов может умножить одновременно материализованные данные.

Планируемая application-нода 16 vCPU / 32 GB и внешняя HA PostgreSQL — следующий испытательный стенд, не подтверждённая ёмкость. Сначала повторить эту матрицу с реальной сетевой задержкой БД, затем согласованный отдельный тест на 5 млн в новом томе и реальные параллельные integrations. Контролировать steady-state и cold cache, I/O, heap fetches, рабочий набор индексов, очереди и память. Дополнительные миллионы в этом раунде не генерировались.

## I. Внедрение и откат

Новые production-файлы: `dojo/product/queries.py`, `dojo/product/ui/views.py`, `dojo/home/views.py`, `dojo/utils.py`, `dojo/metrics/views.py`. Новые/восстановленные тесты: `unittests/test_round4_performance.py`, `unittests/test_local_release_performance_checks.py`. Миграций, новых индексов, глобального кеша и новых production-сервисов нет. Benchmark-only middleware/broker/config не входят в application-патч.

- Для review Round 4: [round4.patch](round4.patch). Для релиза 3.5.100 со всеми этапами: [cumulative_performance.patch](cumulative_performance.patch).
- Нормализация версии в интеграционном коммите нужна для этого сравнения; при переносе на актуальный upstream dev не переносить несвязанные release-normalization изменения вслепую.
- Перед внедрением прогнать тесты на целевой ветке, проверить counts/sort/permissions и source hashes, повторить workload на целевой инфраструктуре.
- Сортировка Products UI по finding count сохраняет прежний подзапрос; максимальный выигрыш относится к стандартной сортировке.
- [Воспроизведение](REPRODUCE.md) · [Безопасный rollback](ROLLBACK.md). Основной 8080 этим исследованием не заменялся. После тестов восстановлены три ранее работавших benchmark-приложения. На 48084 оставлена FINAL read-only тестовая сборка на исходной БД без измерительного middleware; import worker/broker остановлены. [Итоговое состояние](final_checks.json).
'''
(R/'FINAL_PERFORMANCE_REPORT.md').write_text(report)
summary=f'''# Результаты оптимизации DefectDojo 3.5.100

Исходный DefectDojo и наш форк проверены на одном MacBook M5 с 16 GB RAM, одном локальном PostgreSQL и **{F['findings']:,} findings**. Исходная версия восстановлена из официального тега, все сборки имеют проверенные Git SHA и одинаковые зависимости. Основная база сохранена; контрольный хэш всех finding-строк совпал со снимком до испытаний.

## Что удалось доказать

На фиксированном смешанном workload с полными стандартными ответами API и основными серверными страницами при 25 параллельных запросах:

| Показатель | Original | Итоговый форк |
|---|---:|---:|
| Throughput | {original['rps']:.2f} RPS | {final['rps']:.2f} RPS |
| HTTP p95 | {original['p95_ms']/1000:.2f} с | {final['p95_ms']/1000:.2f} с |
| Ошибки | 0% | 0% |

**Производительность выросла в {final['rps']/original['rps']:.2f} раза; p95 снизился на {-pct(original['p95_ms'],final['p95_ms']):.1f}%.** Отдельно от уже накопленных исправлений Round 1–3, Round 4 увеличил mixed throughput с {current['rps']:.2f} до {final['rps']:.2f} RPS. Измерено {primary:,} read-only запросов с прогревом и двумя раундами в обратном порядке. Дополнительная модель использовала 25 независимых аккаунтов с think time.

## Что изменено

Ранее были устранены повторные SQL-запросы Findings, ускорены Products и связанные Jira-данные Tests, добавлены явные облегчённые Product-режимы и экспериментальная глубокая пагинация.

Round 4 исправил три других участка: повторные агрегаты Products UI, повторную обработку статистики Dashboard и загрузку полных findings ради чисел в Simple Metrics. Изменения небольшие, сохраняют точные счётчики и стандартный формат данных.

Свежий единый benchmark показал:

- Products API, полный стандартный список: p95 {metric('endpoints','original','products',1)['p95_ms']/1000:.2f} → {metric('endpoints','final','products',1)['p95_ms']/1000:.2f} с.
- Products UI: p95 {metric('endpoints','original','web_products',1)['p95_ms']/1000:.2f} → {metric('endpoints','final','web_products',1)['p95_ms']/1000:.2f} с.
- Dashboard: p95 {metric('endpoints','original','dashboard',1)['p95_ms']/1000:.2f} → {metric('endpoints','final','dashboard',1)['p95_ms']/1000:.2f} с.
- Формирование нового Simple Metrics отчёта: p95 {metric('endpoints','original','simple_metrics_cold',1)['p95_ms']/1000:.2f} → {metric('endpoints','final','simple_metrics_cold',1)['p95_ms']/1000:.2f} с. Уже кешированная страница измерялась отдельно.

Эти цифры не получены сложением результатов прежних раундов. Основной mix использует полные Product-ответы; облегчённый JSON не выдавался за такую же нагрузку.

## Как проверена корректность

92 автоматизированных теста прошли, 8 штатно пропущены. Совпали {json_pairs} пары полных JSON и {html_pairs} пары проверяемых HTML-контекстов. Проверены права доступа, сортировка, пагинация, фильтрация и связанные vulnerability IDs. На трёх идентичных копиях выполнены 54 настоящих import/reimport POST с дедупликацией внутри крупного Product, а также {bg:,} запросов чтения. Дубликаты и evidence проверены непосредственно в БД.

## Что это даёт платформе

Есть воспроизводимое доказательство выигрыша нашего форка относительно исходного DefectDojo в конкретных пользовательских сценариях. Сохранены совместимость и возможность отката без миграции данных. Результаты можно повторить по сохранённым скриптам, исходным наблюдениям и графикам. Другие ASPM-продукты в сопоставимых испытаниях не участвовали.

## Что нужно до production

Текущий Mac подтверждает улучшение кода, но не ёмкость production на 20 млн findings. При c=25 сохраняются многосекундные задержки. Основные ограничения — точный COUNT, полные списки finding IDs, PostgreSQL/Python CPU и память под конкуренцией. Синтетическая база менее насыщена связями и evidence, чем production.

Следующий обязательный этап — серверный стенд с планируемой app-нодой 16 vCPU / 32 GB и внешней HA PostgreSQL, затем отдельное согласованное испытание на 5 млн с реальными сканерами и сетевой задержкой БД. Потребители API должны осознанно выбирать count/summary там, где им не нужен полный список IDs. Готовность к production и SLA требует этих испытаний.

[Полный отчёт и графики](FINAL_PERFORMANCE_REPORT.md) · [Данные](benchmark_results.csv) · [Воспроизведение](REPRODUCE.md)
'''
(R/'EXECUTIVE_SUMMARY.md').write_text(summary)
print('Filled technical report and executive summary generated')
