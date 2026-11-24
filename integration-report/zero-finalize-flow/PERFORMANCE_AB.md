# Производительность A/B

A — точный integration `19cd7b4129de52e75eabaf0e07739e4c2b682f8e`; B — `12dfcbe6bb0beb1cbe0bd411b2c26b820cb9d23a`. Новые результаты сняты последовательно на одинаковых независимых копиях своей baseline fixture DB, после завершения full suites/functional traffic. CPU2 / RAM1536MiB для app; PostgreSQL CPU1 / RAM768MiB; ARM64. Immutable production images проверены по всем tracked dojo Git blobs.

## Малый диагностический A/B

Метод: in-process Django client + настоящий PostgreSQL/importer; 6 ScanRuns × 100 findings; UI 1 warmup + 20 measured requests; 3 явных generated exports. Это не network/queue latency, не 1M stand, не frozen Core9/mandatory acceptance и не доказательство p95 production traffic.

| Метрика | A | B |
|---|---:|---:|
| Acceptance median, ms | 16.951 | 17.108 |
| Completion median, ms | 622.481 | 620.269 |
| Overview median, ms | 6.153 | 11.293 |
| Findings median, ms | 8.409 | 12.731 |
| Live ASPM Report median, ms | 6.764 | 11.143 |
| Snapshot median на 100 findings, ms | 8.100 | 8.133 |
| Fixation + report registration median, ms | 5.976 | 4.366 |
| Generated HTML + JSON median, ms | 17.234 | 15.631 |
| Process CPU, s | 1.799 | 2.102 |
| Process peak RSS, KiB | 221640.000 | 221028.000 |
| Observations relation + indexes, bytes | 638976.000 | 638976.000 |

Overview: **13 → 23 SQL queries/request**; Findings **13 → 22**, live ASPM Report **13 → 23**. Новая страница выполняет дополнительный bounded выбор context/актуальных runs, показывает live summaries и ограниченный CWE/CVE preview. Абсолютная добавка Overview около 5.14ms в этой малой диагностике; она явно сохранена как стоимость нового поведения. A не отображает эквивалентную live сводку. Эти результаты не обосновывают масштабирование на миллион observations.

Acceptance SQL counts одинаковы (14/26, включая первый cold context). Completion query sets A 667/670, B 668/669; новая shared-environment metadata lock добавляет короткий запрос, при этом parsing/Finding transaction protocol не изменён. Автоматического snapshot/export после каждого scan нет.

Generated JSON последней версии: 61,271 → 61,771 bytes; HTML: 102,604 → 103,549 bytes. Дополнительный объём — frozen selection provenance. Observations relation одинакова 638,976 bytes; всего 600 historical observations на build. Старые report versions не перезаписываются.

[Raw A](checks/small-ab-a.json), [Raw B](checks/small-ab-b.json). App CPU/RSS относятся к benchmark process, не Celery peak worker RSS. PostgreSQL CPU, queue latency, concurrent throughput и WAL в целевом масштабе здесь не измерены. Конкурентная корректность отдельно проверена настоящими threads/worker faults; это не throughput benchmark.

## Полный performance gate

Frozen Core9 + mandatory acceptance A/B на immutable 1M seed **не запускался**: available 7,860,330,496 bytes, guard requires 13,096,679,103 (6 GiB floor + 4,506,744,511-byte seed + 2 GiB buffer). Guard не ослаблялся. 5–20 млн на MacBook не запускались. Старые Mac/RC4 measurements, включая 72.924s / 17.001s, не используются как новые результаты.

[Disk evidence](checks/performance-disk-gate.json). Полный performance release gate остаётся HOLD до достаточного disk budget/стенда и свежего frozen campaign.
