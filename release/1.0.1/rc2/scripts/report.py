"""Fill release reports from the recovered, reproducible evidence only."""
import json
from collections import Counter
from pathlib import Path
from common import OUT, ROOT, SOURCE, VARIANTS

assert (OUT/'raw/verification-complete.json').exists()
rows=json.loads((OUT/'benchmark_results.json').read_text())
tests=json.loads((OUT/'raw/full-test-summary.json').read_text())
images=json.loads((OUT/'build.json').read_text())['variants']
data=json.loads((OUT/'raw/dataset-final.json').read_text())
compat=json.loads((OUT/'compatibility.json').read_text())
browser=json.loads((OUT/'raw/browser-validation.json').read_text())
expanded=json.loads((OUT/'raw/browser-expanded.json').read_text())
matrix=json.loads((OUT/'raw/ui-matrix.json').read_text())
imports=json.loads((OUT/'raw/import-verification.json').read_text())
baseline=json.loads((OUT/'raw/baseline-tests-complete.json').read_text())
mixed={v:next(x for x in rows if x['phase']=='mixed' and x['concurrency']==25 and x['variant']==v) for v in VARIANTS}
endpoint={v:{x['case']:x for x in rows if x['phase']=='endpoints' and x['variant']==v} for v in VARIANTS}
total=sum(x['n'] for x in rows)
names={'round5':'Round 5','rc1':'RC1','rc2':'RC2'}


def number(value,scale=1):
    return f'{value*scale:.3f}' if value is not None else 'н/д'


def write(name,text):
    (ROOT/'release/1.0.1'/name).write_text(text.strip()+'\n')


table='| Показатель, c25 | Round 5 | RC1 | RC2 |\n|---|---:|---:|---:|\n'
for label,key,scale in [('Mixed p50, s','p50_ms',.001),('Mixed p90, s','p90_ms',.001),('Mixed p95, s','p95_ms',.001),('Mixed p99, s','p99_ms',.001),('Mixed RPS','rps',1),('PostgreSQL CPU, % (100%=ядро)','pg_cpu_mean_pct',1),('uWSGI CPU, %','app_cpu_mean_pct',1),('App container peak, MiB','app_container_peak_mib',1),('Один worker peak RSS, MiB','worker_rss_peak_mib',1),('Среднее SQL execute/request, ms','mean_sql_ms',1)]:
    table+='| '+label+' | '+' | '.join(number(mixed[v][key],scale) for v in VARIANTS)+' |\n'
table+='| HTTP errors | '+' | '.join(str(sum(n for status,n in mixed[v]['statuses'].items() if status!='200')) for v in VARIANTS)+' |\n'
table+='| Наблюдения / повторы | '+' | '.join(f"{mixed[v]['n']} / {mixed[v]['repeats']}" for v in VARIANTS)+' |\n'
ranges='| Вариант | p95 повторов, s | RPS повторов |\n|---|---|---|\n'
for v in VARIANTS:
    ranges+=f"| {names[v]} | "+', '.join(number(x['p95_ms'],.001) for x in mixed[v]['runs'])+' | '+', '.join(number(x['rps']) for x in mixed[v]['runs'])+' |\n'
latency_change=(mixed['rc2']['p95_ms']/mixed['round5']['p95_ms']-1)*100
rps_change=(mixed['rc2']['rps']/mixed['round5']['rps']-1)*100
interpretation=f"RC2 относительно Round 5: p95 {latency_change:+.2f}%, RPS {rps_change:+.2f}%. Это описательное сравнение трёх повторов, а не доказательство статистической значимости."
if abs(latency_change)<=10 and abs(rps_change)<=10:
    interpretation+=' Оба отклонения укладываются в ориентир ±10%; доказанной существенной регрессии в этой серии не установлено. Ускорение RC2 не заявляется.'
else:
    interpretation+=' Ориентир ±10% превышен как минимум по одной метрике; перед допуском требуется дополнительное расследование. Ускорение RC2 не заявляется.'

end_table='| Endpoint (c1, n=120/build, 2 повтора) | R5 p95, s | RC1 p95, s | RC2 p95, s | SQL R5/RC1/RC2 | Bytes RC1/RC2 |\n|---|---:|---:|---:|---|---|\n'
for case in endpoint['round5']:
    xs=[endpoint[v][case] for v in VARIANTS]
    end_table+='| '+case+' | '+' | '.join(number(x['p95_ms'],.001) for x in xs)+' | '+' / '.join(str(x['median_sql_count']) for x in xs)+' | '+f"{xs[1]['mean_bytes']:.1f} / {xs[2]['mean_bytes']:.1f}"+' |\n'

write('RC2_PERFORMANCE.md',f'''# ASPM 1.0.1 RC2 — контролируемая performance-проверка

Измерения выполнены заново 12 ноября 2026 на одном Mac M5/16 GiB, Docker VM 10 CPU/7.82 GiB, PostgreSQL 18.6, uWSGI 4 processes × 4 threads. Лимиты контейнеров, версии Python/Django/DRF и всех dependencies одинаковы; см. [environment](rc2/raw/environment.json), [dependencies](rc2/raw/dependencies.json), [images](rc2/build.json). DEBUG=false. Конфигурация сервера не настраивалась ради результата.

## Методика

Один protected seed `dd_round4_seed`: **1 000 168 findings**. Ни миграций, ни worker/beat над seed; подготовка auth добавляет только session rows, не меняя findings/products/memberships. Основная source читается только для fingerprint. 25 существующих identities (1 admin, 24 scoped), concurrency — число одновременных HTTP requests, не число независимых виртуальных пользователей. Think time=0; акторы распределены тем же генератором и seeds35101/35102/35103. Это saturation test, не моделирование 25 людей.

45 mixed runs: c1/5/10/15/25 × 3 builds × 3 repetitions, 300 measured +25 warmup/run. Порядок ABC/BCA/CAB. 60 endpoint runs: 10 routes ×3 builds ×2 repeats, 60 measured +5 warmup, c1. Всего **{total:,} measured requests**; все сохранены в [raw](rc2/raw), [JSON](rc2/benchmark_results.json), [CSV](rc2/benchmark_results.csv). Warmup не входит в percentiles/RPS. Неполный подготовительный прогон с manual stop сохранён отдельно в [excluded](rc2/excluded/preflight-paused/reason.json); он не является performance-серией. Ранее утраченные `/private/tmp` результаты не подмешаны, см. [recovery](rc2/RECOVERY.md).

Workload не изменён: Findings30%, Product/severity/active filter15%, detail10%, **full Products10%**, Tests10%, Engagements5%, Dashboard10%, Products UI5%, Endpoints5%; page limit100. `findings=count`, `none`, FAST проверены отдельно, не подменяют полный ответ.

## Новая сопоставимая серия

{table}
{ranges}
{interpretation}

Общий p95 вычислен из объединённых observations, не как среднее p95. RPS=Σrequests/Σelapsed. p99 только при n≥300; per-case mixed p95 только при n≥20. Разброс повторов виден в таблице, JSON и графиках; линии не сглажены. Для SQL: client execute wall time включает ожидание БД и передачи, не является PostgreSQL CPU time. `pg_stat_statements` недоступен; global settings не менялись. Buffers/temp counters и connections записаны монитором по реальному DB scope; это sampled deltas, не полные per-query server totals. RSS одного worker и сумма RSS не равны физической памяти из-за shared pages. CPU100%=одно логическое ядро.

## Отдельные маршруты

{end_table}
Полные p50/p90/p95, RPS, SQL count/time, response bytes, worker RSS, connections, buffer/temp deltas и repeat observations — в JSON. Для коротких HTTP-сценариев resource sampling может отсутствовать; такие значения остаются null. SQL plans: [R5](rc2/plans-round5.json), [RC1](rc2/plans-rc1.json), [RC2](rc2/plans-rc2.json), безопасные SELECT EXPLAIN ANALYZE BUFFERS без credentials/bindings.

## Графики

![p95](rc2/charts/p95-vs-concurrency.png)
![RPS](rc2/charts/rps-vs-concurrency.png)
![Critical endpoints](rc2/charts/critical-endpoints.png)
![PG CPU](rc2/charts/postgresql-cpu.png)
![SQL time](rc2/charts/sql-time.png)
![Before/After](rc2/charts/before-after-endpoints.png)

Дополнительно: SQL count и worker RSS в `rc2/charts`. Генератор `rc2/scripts/plot.py` читает JSON. Browser navigation timings записаны отдельно: [16 cold/warm navigations](rc2/raw/browser-performance.json), descriptive samples без p95-заявления; они включают CSS/JS и не смешаны с server-side HTTP latency.

Исторические 3.077s/20.57RPS (R5) и 5.01s/19.81RPS (RC1) относятся к другим сериям. Они не используются для вывода о регрессии и не входят в приведённую таблицу. External PostgreSQL и app node16vCPU/32GiB не испытывались.

Проверены historical environment snapshots: те же10 Docker CPU/7.82GiB, Python3.14.8/Django5.2.17/DRF3.18.3, DEBUG=false, CONN_MAX_AGE=0 и отсутствие per-container limits. В старых snapshots swap составлял1982.25/2174.75MiB, в новой mixed-серии0MiB. Такие snapshots могут описывать уже возвращённый demo после writes; они не доказывают DB scope конкретного старого load run. Причину старой разницы p95 по этим данным изолировать нельзя. Новая серия фиксирует DB scope/versions/settings/schedule непосредственно. [Сопоставление окружений](rc2/raw/historical-environment-comparison.json), [фактический финальный runtime](rc2/raw/actual-runtime.json).
''')

skip_counts=Counter(x['reason'] for x in tests['skip_details'])
skip_text='\n'.join(f'- {count}: {reason}' for reason,count in skip_counts.most_common(7))
red='\n'.join(f"- `{x['name']}`: methods={x['run']}, passed={x['passed']}, failure entries={x['failures']}, error entries={x['errors']}, skipped={x['skipped']}." for x in baseline['runs'])
write('RC2_TEST_RESULTS.md',f'''# ASPM 1.0.1 RC2 — regression evidence

Источник runtime: `{SOURCE}`. Штатный `./run-unittest.sh --test-case unittests`, отдельный retained PostgreSQL/Valkey проекта `dd-final-tests`, internal offline network. Основная БД и validation-копия test runner не используются.

## Полный Django discovery

**{tests['tests_run']} run; {tests['passed']} passed; {tests['assertion_failures']} assertion failures; {tests['errors']} import errors; {tests['skipped']} skipped.** [Машиночитаемые outcomes/skip reasons](rc2/raw/full-test-summary.json). Suite не зелёный; эти errors не скрыты и не превращены в skips.

Два blockers воспроизведены на frozen R5 и RC1:

- `unittests.test_ticket_comments` требует отсутствующий `dojo.notifications.ticket_comments`.
- `unittests.tools.test_trufflehog_parser` требует отсутствующий `unique_id_from_tool`.

[Version-origin evidence](rc2/raw/test-version-origin.json): теста ticket_comments в чистом3.5.100 нет; исходный TruffleHog test не требует нового helper. Внедрение будущей notification/dedup семантики выходит за запрет на функциональные изменения. Не добавлены stubs, новые skips или удаление тестов.

Наиболее частые существующие skips (все553 причины перечислены в JSON):

{skip_text}

## Новые guards и red/green

17 новых Django tests: 9 общей UI pagination, 6 Product filters/RBAC, 2 collection pagination. Дополнены существующие metadata checks. 3 новых Select2 cases; всего **12/12 Node tests passed**, 0 fail/skip. Строгий Ruff изменённых runtime/test файлов passed.

Эти же12 Node cases на frozen RC1 JS дают9 pass/3 fail: [red evidence](rc2/raw/javascript-red-summary.json). Новые guards действительно обнаруживают прежние ошибки.

{red}

В red baseline error/failure entries могут включать subtests; их нельзя складывать с числом методов. Полный suite выше содержит два отдельных loader errors.

Root cause grade test flakiness: debounce marker переживал database rollback и переиспользование Product PK между fixture cases. Очистка только соответствующего cache key в setup/cleanup теста устранила зависимость от порядка; **query assertions285/311/75/172 и production debounce не менялись**. Offline Jira DNS test принимает библиотечный NameResolutionError для `.invalid`; реальное соединение по-прежнему должно завершиться ошибкой.

## API / UI / import

- {compat['pairs']} сопоставимых пар: {compat['complete_json_pairs']} полных JSON hashes (включая {compat['expected_denial_pairs']} ожидаемых403 denial pairs для users/notes без global permissions) и {compat['pairs']-compat['complete_json_pairs']} HTML semantic comparisons. Ошибок сравнения: {len(compat['failures'])}. Изменения только порядка ранее неупорядоченных UI ties отдельно перечислены и проверены по одинаковым первичным sort values; standard API order/data/bytes совпадают. Диагностический collector первоначально читал sort metadata после prefetch; исходная попытка и corrected recapture сохранены в `rc2/diagnostics/prefetch-order-metadata`. Это не изменение измеренных load samples.
- Standard/FAST pagination, Product count/none, filtering, sorting, permissions, vulnerability references, Dashboard/Simple Metrics и предыдущие R1–5 guards входят в полномасштабный discovery/profiles.
- Browser: {len(browser['rows'])} страниц/theme/viewport состояний, {len(browser['checks'])} функциональных checks; failures={len(browser['failures'])}. Реальные Chromium143/Playwright1.57/axe4.14; screenshots в `rc2/screenshots`. Expanded dark filters: {len(expanded['rows'])} desktop/mobile states, no axe/console violations. Light/Dark/System, sidebar keyboard, forms/dropdowns/navigation/selection проверены. [P0 before](rc2/raw/browser-p0-before.json) / [after](rc2/raw/browser-p0-after.json).
- Server pagination matrix: {matrix['checks']} проверок first/next/previous/last, missing/bad/negative/huge page, size50/invalid, filters/sort/empty, prefix Test page и admin/restricted; count, ranges, uniqueness, no adjacent overlap. [Matrix](rc2/raw/ui-matrix.json).
- Дополнительно6 desktop/mobile ×Light/Dark/System states и24 быстрых Next/Next/Prev/Prev перехода: фильтры, состав страниц и тема сохраняются; реальные generated Select2 controls обнаружены, JS errors0. [Rapid navigation](rc2/raw/browser-rapid.json).
- Browser CSRF create/edit, invalid/valid login, access-free denial: 5 checks. Дополнительные actual HTTP foreign-Product filter/FAST/ordering для access-free пользователя: count0. UI legacy denial status400 с403 body отдельно сохранён как inherited issue; API403/404 и отсутствие утечки подтверждены.
- Реальные ZAP import/reimport/duplicate peer: 3×201, deduplication_complete=true. Primary{imports['primary_count']} scanner findings, mitigated{imports['mitigated']}, peer{imports['peer_count']}, duplicates{imports['peer_duplicates']}; связанность и две actual vulnerability-reference rows в browser finding подтверждены. Флаг deduplication изменялся и восстановлен только на write-copy.
- Actual image rollback RC1↔RC2: 18 полных JSON pairs equal, worker остановлен на время переключения; очередь после=0, RC2 восстановлен.
- Django check, migration dry-run и OpenAPI --fail-on-warn passed; новых migrations нет. Финальные app/worker logs без ERROR/Traceback, OOM=false. Legacy Selenium suite не исполнялась: Selenium/chromedriver отсутствуют в test image; реальная браузерная проверка выше выполнялась через Playwright. Непроверенные acceptance400/10VU и external-node benchmarks не выдаются за выполненные.
''')

write('RC2_GIT_PROVENANCE.md',f'''# Git / Docker provenance — ASPM 1.0.1 RC2

Рабочая ветка `release/1.0.1-rc2`, создана от проверенного RC1; исходный пользовательский checkout `feature/ha-orm-scm-engagements-ui-webhooks` на207c7740bcd9ac56bd8a496ad30aca3778b41b7b и его untracked файлы сохранены. Новый origin/dev или custom Engagements код не подмешивался.

## Почему RC1 имел два SHA

RC1 release HEAD `d153d109706749d4e7910e0c585a9ac760b98eba`; embedded source `5cdbc77fc9d4b8d0899069f5d44cd5241b2acae6`. Между ними release docs, QA evidence/helpers и packaging recipes; **нет изменений embedded dojo, static и dependency runtime**. Называть всю разницу только документацией было бы неточно. [Полный список путей и runtime comparison](rc2/raw/rc1-provenance.json).

Recipes могут влиять на запуск, поэтому сравнение использовало одинаковые фактические4×4 uWSGI, limits/env и pinned dependencies; labels отдельно не считались достаточной проверкой. [Actual runtime](rc2/raw/actual-runtime.json). В environment унаследован DD_INITIALIZE=true, но Compose запускает только явно указанные app/nginx/cache/worker, initializer service отсутствует и migrations не выполнялись.

## Источники сопоставимой серии

| Variant | Runtime source | App image ID | Nginx ID |
|---|---|---|---|
'''+''.join(f"| {names[v]} | `{VARIANTS[v][2]}` | `{images[v]['app']['id']}` | `{images[v]['nginx']['id']}` |\n" for v in VARIANTS)+f'''
## RC2

ASPM version **1.0.1**, channel **rc2**; upstream DefectDojo **3.5.100**. Frozen source **`{SOURCE}`**. `get_branding`, image ENV и OCI revision соответствуют ему. OCI created/DD_ASPM_BUILD_TIMESTAMP нормализованы к SOURCE_DATE_EPOCH (`2026-11-11T21:27:27Z`) для воспроизводимости; фактическое capture время — environment.json. Upstream internal version не переименована.

Проверены2233 app source/compiled files и40 tracked static files, mismatches0. Повторная сборка после восстановления дала **те же app/nginx content IDs**: [reproduced build](rc2/build-reproduced.json), [identity check](rc2/raw/build-reproducibility.json). Base dependencies закреплены digest в build-lock.json; GNU msgfmt и все28 translations записаны в manifest. Python dependencies идентичны трём вариантам.

Позднейшие RC2 commits содержат QA scripts, raw evidence и release docs. Их HEAD может отличаться от runtime source; проверять `git diff {SOURCE}..HEAD -- dojo components requirements.txt requirements-dev.txt Dockerfile.django Dockerfile.nginx`: runtime diff должен быть пуст. Для Docker build всегда указывать точный sourceSHA, не изменяющийся HEAD.

RepoDigest отсутствует: images локальные, registry push не выполнялся. Приведён content image ID, не вымышленный registry manifest digest. Alias `aspm:1.0.1-rc2` и Stable1.0.1 **не promoted** из-за двух full-suite import errors. Кандидат доступен как `aspm-build:25fb63ae7b48` / `aspm-nginx-build:25fb63ae7b48`; его byte identity фиксирована IDs выше.
''')

write('RC2_KNOWN_ISSUES.md',f'''# ASPM 1.0.1 RC2 — оставшиеся ограничения

1. **Release blocker:** два унаследованных discovery import errors (ticket_comments / TruffleHog helper), воспроизводятся также R5/RC1. Требуется отдельное согласованное выравнивание test/runtime version; нельзя добавлять новую notification/dedup логику или отключать тесты для получения зелёного suite.
2. Унаследованный HTML unauthorized handler возвращает400 с403 Forbidden body; API403/404 и отсутствие чужих findings подтверждены. Статус не менялся в этом hardening scope.
3. 553 conditional/legacy skips перечислены поимённо; среди них один известный legacy UI Engagement move-to-authorized-Product case (API path покрыт, UI business workflow здесь не менялся). Legacy Selenium suite недоступна в image. Playwright-проверки выполнены реально; это не заявление о запуске Selenium.
4. Exact COUNT, OFFSET и полный Product findings ID list сохраняют стоимость, растущую с данными/response size. Opt-in count/none и FAST сохранены, не включены глобально. PK tie-break делает порядок стабильным при неизменной БД; OFFSET не создаёт snapshot между запросами при concurrent writes.
5. {interpretation} Измерения ограничены M5/16GiB и1млн преимущественно синтетических findings; генератор пропускал часть signals/dedup/relations. Небольшой реальный scan smoke не делает датасет полноценным production. Production15–25 людей, HA PostgreSQL и16vCPU/32GiB node не сертифицированы этим тестом.
6. Локальный stand не заменяет production security/TLS/secret management. Stable/RC2 alias не опубликованы. Четыре будущих acceptance-теста400 findings/10VU, create/open/export не запускались как отдельная сертификационная матрица.

Ранее утраченные временные raw не восстановлены из памяти: итог использует только новую сохранённую серию. Все остановленные/исключённые подготовительные наблюдения сохранены с причиной в rc2/excluded.
''')

perf_gate=('PASS: нет доказанной существенной регрессии; разброс опубликован' if abs(latency_change)<=10 and abs(rps_change)<=10 else 'REVIEW: отличие превышает ориентир, см. performance report')
gates=[('Product-фильтр, reset/navigation, scopes','PASS'),('UI pagination boundaries/count/order','PASS'),('RBAC/Product membership/no foreign data','PASS'),('Все обязательные и доступные Django tests','BLOCKED: 2 inherited import errors; 8111 pass, 553 skip'),('Import/reimport/dedup на write-copy','PASS'),('R1–5 guards/API compatibility','PASS'),('Контролируемая performance-серия',perf_gate),('Image source/static/dependencies/provenance','PASS'),('Light/Dark/System / real browser','PASS'),('Release notes/rollback','UPDATED'),('Основная БД1 000 168 и seed целы','PASS'),('Known limitations','DOCUMENTED'),('Promote aspm:1.0.1-rc2 / Stable','NOT PERFORMED')]
write('RC2_RELEASE_CHECKLIST.md','# ASPM 1.0.1 RC2 — release gates\n\n**Статус: кандидат подготовлен, формальный release gate не пройден.**\n\n| Gate | Result |\n|---|---|\n'+''.join(f'| {k} | {v} |\n' for k,v in gates)+'\nДва errors нельзя заменять skips/stubs. После их корректного устранения повторить full suite, соответствующие guards и provenance; только затем promote immutable alias по content ID. Stable1.0.1 отдельно не публиковать без приёмки.\n')

write('RC2_REPORT.md',f'''# ASPM 1.0.1 RC2 — release hardening

**Кандидат подготовлен, формальный выпуск заблокирован двумя унаследованными test import errors.** Все runtime исправления в отдельных commits на `release/1.0.1-rc2`; frozen image source `{SOURCE}`. Данные основной БД **1 000 168 findings** и protected seed сохранены по count/sum/full-row fingerprints. Изолированная write-copy теперь содержит {data['databases']['aspm_rc2_validation']['findings']:,} findings; исходный prefix также неизменен.

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

{table}
{interpretation}

Новая серия: {total:,} HTTP requests, {len(rows)} pooled scenarios, 105 runs; c25 по3 repeats/build. Исторические серии не подмешаны. HTTP errors в проверенной серии: {sum(sum(n for status,n in x['statuses'].items() if status!='200') for x in rows)}. [Методика/таблицы/графики](RC2_PERFORMANCE.md), [raw JSON](rc2/benchmark_results.json).

## Проверки и статус

Django: {tests['passed']} passed, {tests['assertion_failures']} assertion failures, {tests['errors']} import errors, {tests['skipped']} skipped, total{tests['tests_run']}. Node12/12; Ruff passed. {compat['pairs']} full JSON/HTML semantic comparisons;18 rollback JSON pairs; browser{len(browser['rows'])} page/theme/viewport states +{len(browser['checks'])} controls, expanded filters2; server pagination{matrix['checks']} checks; real ZAP3×201 +dedup, actual CSRF create/edit/login and two vulnerability references. Проверки выполнены реально, не выведены из HTTP200/count alone.

Два blockers не исправлены добавлением новых интеграций или изменением дедупликации. См. [test results](RC2_TEST_RESULTS.md), [known issues](RC2_KNOWN_ISSUES.md), [gates](RC2_RELEASE_CHECKLIST.md). Кандидат можно исследовать локально на48091; статус «Release Ready»/Stable не присвоен.

## Исходники, доставка, rollback

App ID `{images['rc2']['app']['id']}`; nginx ID `{images['rc2']['nginx']['id']}`. Локальные images, registry digest отсутствует. Проверено2233 app files/40 static files, reproducible content IDs; [provenance](RC2_GIT_PROVENANCE.md). RC1 HEAD/source различались из-за QA/packaging/docs, embedded runtime не расходился.

Список изменений: [changed files](rc2/changed_files.md). [Reproduce](rc2/REPRODUCE.md), [build](BUILD.md), [deployment](DEPLOY.md), [rollback](ROLLBACK.md). Никаких destructive DB операций или изменения исходных findings. Следующие400-findings/10VU и external-node испытания не выполнялись и остаются отдельным этапом.
''')
print('Filled all six RC2 reports from saved measured evidence; candidate remains gated')
