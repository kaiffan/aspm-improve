# Производительность

## Историческая HA Stabilization

Приложение eee10e678c77, chart rc.8, небольшой синтетический датасет на одном ARM64 узле, PostgreSQL 18.6. Baseline rc.7 дал 84,50 → 126,71 GET RPS и 2,98 → 3,83 ScanRuns/s (1/1 → 2/3, равный бюджет), acceptance p50 78,65 → 255,67 ms. Старый прогон не измерял поэтапное время.

| Режим, предложено 75 GET/s × 16 s | HTTP 200 | Клиент p50 ms | API p50 ms | Django p50 ms |
|---|---:|---:|---:|---:|
| A, 1 web / 1 worker | 1101 | 116,34 | 25,54 | 32,30 |
| B, 2/3, равный общий бюджет | 1200 | 164,71 | 67,02 | 86,20 |
| C, 2/3, web limit 2 CPU вместо 1 на Django | 1200 | 123,10 | 50,64 | 66,12 |

По 24 уникальных JSON upload, три параллельно, шесть GET readers. B/C доставили одинаковую интенсивность. Изменение лимита снизило клиентскую медиану на 25%, API на 24%, throttled periods 28/368 → 11/366 и throttled time 7,46 → 2,76 с. SQL/rate limit, fsync и repo/commit SQL выросли при throttling. Сравнение использовало ClusterIP и диагностический image. Отдельный Loopback TLS прогон 12/12 HTTP 202 дал 33,92 ms клиент p50 и 19,38 ms handler.

Исторический максимум PostgreSQL — 13 сессий, 5 активных, 3 Lock waits, 3 idle in transaction на 8667 сэмплах. Exact COUNT, commit overview, large reports, memory Product Metrics и конкурентные writes покрываются направленной регрессией. Пределы требуют измерений на рабочем workload. [Ресурсы и параметры](../docs/03_SYSTEM_REQUIREMENTS.md)

## 1M и capacity

Core9/Acceptance 1M, 15–25 активных пользователей и многомиллионная ёмкость остаются отдельной проверкой. Доступная площадка — один Linux/ARM64 узел с 10 vCPU и около 8 GiB RAM. Для квалификации нужен согласованный стенд с достаточными I/O, местом для копий БД и полным бюджетом 16 vCPU/32 GiB приложения сверх внешних зависимостей. [План нагрузки](benchmark/README.md)

## Повтор на bef347c845ee

Один запуск на вариант после готовности всех реплик, тот же выделенный PostgreSQL и private storage, ClusterIP HTTP. 6 читателей, предлагаемые 75 GET/с × 16 с, 24 small JSON uploads по три параллельно, проверены COMPLETED и один Finding на запуск. A и B имели одинаковые суммарные requests и limits, включая Django / nginx / worker. A использовал один worker с concurrency 3, B и C — три с concurrency 1. Лимит одного Django был 2 CPU в A, 1 CPU в B, 2 CPU в C. C менял только Django limit относительно B.

| Метрика | A 1/1 | B 2/3, равный бюджет | C 2/3, дополнительный CPU web |
|---|---:|---:|---:|
| GET 200 / эффективный RPS | 1200 / 75 | 1200 / 75 | 1200 / 75 |
| GET p50 / p95 / p99, ms | 19,44 / 43,25 / 56,70 | 16,66 / 32,77 / 77,43 | 17,54 / 40,57 / 67,90 |
| Accept client p50 / p95 / p99, ms | 32,54 / 70,34 / 78,11 | 23,12 / 53,18 / 73,13 | 37,61 / 64,93 / 67,21 |
| Accept API p50 / p95 / p99, ms | 14,85 / 30,43 / 44,40 | 15,22 / 37,96 / 43,19 | 16,59 / 40,14 / 44,62 |
| Queue wait p50, ms | 13,43 | 12,88 | 19,35 |
| Accepted / Completed | 24 / 24 | 24 / 24 | 24 / 24 |
| Полное окно наблюдения, с | 16,122 | 16,135 | 16,156 |
| CPU workload, с, Django + worker | 9,93 | 11,25 | 12,89 |
| Сумма memory.peak контейнеров, MiB, Django + worker | 1031 | 1819 | 1886 |
| DB connections до/после | 3 / 6 | 3 / 7 | 5 / 7 |
| WAL, bytes | 1 490 870 | 1 150 079 | 2 163 072 |
| PostgreSQL blocks read / cache hit, delta | 2 / 598 083 | 0 / 652 384 | 0 / 704 881 |
| HTTP/TCP errors и failed ScanRuns | 0 | 0 | 0 |

Нагрузка ограничена предложенными 75 GET/с и 24 загрузками, поэтому результаты не описывают максимум RPS или completion rate. CPU и сумма high-water marks относятся к cgroups Django/worker и включают накладные расходы между двумя сэмплами. PostgreSQL connections сняты до/после, исторический пик 13 вынесен выше. Перед переходом B освобождён прежний ReplicaSet worker после завершения A из-за недостатка памяти при overlap. Ресурсы B измерены после Ready для всех трёх workers. В данном малом прогоне деградация прежних 255,67 ms не воспроизведена; B/C не подтверждают устойчивое улучшение от 2 CPU на Django. Для выбора лимита на production нужен повтор на целевой платформе.

[Исходные метрики A](evidence/performance-a.json) · [B](evidence/performance-b.json) · [C](evidence/performance-c.json)
