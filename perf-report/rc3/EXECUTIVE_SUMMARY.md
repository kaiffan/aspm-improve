# ASPM 1.0.1 RC3 — итог

Целевые ориентиры достигнуты в новой сопоставимой серии.
RC2 runtime: `25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb`; release HEAD:
`9384826c2c2ccdbf0178ebc3faa5ea3e5513473d`. RC3 runtime:
`ccfd52d372695176485e65000b4270e01d7dfb1b`. Ветка `perf/1.0.1-rc3-optimization`.

| Показатель | RC2 | Optimized RC3 | Изменение |
| --- | --- | --- | --- |
| Mixed p50, s | 0.760 | 0.642 | -15.5% |
| Mixed p90, s | 1.710 | 1.609 | -5.9% |
| Mixed p95, s | 5.514 | 2.080 | -62.3% |
| Mixed p99, s | 10.302 | 2.708 | -73.7% |
| Throughput, RPS | 17.140 | 28.246 | +64.8% |
| PostgreSQL sampled CPU, % | 527.276 | 580.880 | +10.2% |
| App container peak, MiB | 969.200 | 989.800 | +2.1% |
| SQL execute wall/request, ms | 724.379 | 432.257 | -40.3% |
| HTTP errors | 0 | 0 | 0 |


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

Full Django suite: **8706 run / 8153 passed /
0 failures / 0 errors / 553 прежних skipped**. Оба import blocker исправлены
реальными upstream-реализациями; 12/12 JavaScript tests passed. Полные JSON API:
76 пар; UI contexts: 32 пар; расхождений 0. Реальные browser,
import/reimport/dedup/evidence, pagination и image rollback результаты перечислены
в [TEST_RESULTS](TEST_RESULTS.md).

Оригинал и protected seed: 1 000 168 findings, сумма ID 500168514196,
полный row SHA-256 fingerprint неизменён. Все writes — на отдельной копии.
Локальные Docker image IDs: [build manifest](raw/build-final.json).
Stable не публикуется; ограничения и воспроизведение см. [RESULTS](RESULTS.md),
[REPRODUCE](REPRODUCE.md), [ROLLBACK](ROLLBACK.md).
