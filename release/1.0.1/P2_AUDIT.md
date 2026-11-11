# P2: целевой аудит после UI

Измерено на той же копии 1 000 168 findings. 6 профилей (admin/restricted × Dashboard/Findings/Test); EXPLAIN ANALYZE BUFFERS только для SELECT. Значения одного профиля не являются p95.

| Actor | Page | Wall ms | SQL queries | SQL execute ms | Template inclusive ms |
|---|---|---:|---:|---:|---:|
| 0 | dashboard | 612.1 | 14 | 456.1 | 34.8 |
| 0 | web_findings | 1715.9 | 67 | 1597.0 | 1601.2 |
| 0 | web_test | 1175.7 | 75 | 1067.1 | 996.2 |
| 1 | dashboard | 1062.7 | 15 | 1050.2 | 2.9 |
| 1 | web_findings | 2024.6 | 60 | 1914.5 | 1023.7 |
| 1 | web_test | 1688.5 | 76 | 1579.9 | 991.6 |

Template и QuerySet timings вложенные и могут включать SQL. Их нельзя складывать с SQL как независимые части. Клиентское SQL execute time включает драйвер/ожидание; PostgreSQL execution time берётся отдельно из плана.

## Подтверждённые ограничения

1. Findings UI: `ORDER BY numerical_severity ASC LIMIT 25` выбирает широкую модель, вычисляет SLA annotation и читает большой объём finding-строк. В профиле admin запрос занял 1466 ms (план 1484.824 ms), restricted — 921 ms (план 971.674 ms). Доминирует получение страницы, а не COUNT. Новый narrow-COUNT патч здесь не был бы исправлением главной причины.
2. Test/Findings UI: построение глобальных доступных `DISTINCT title LIMIT 20000` выполняет JOIN по разрешённым Product. Для restricted Test — 530 ms (план 583.677 ms), 633 794 строк до агрегации, 7751 temp written blocks ≈60.6 MiB при block_size=8192. Список не имеет явного порядка. Изменение плана может поменять состав первых 20 000 title; AJAX/ограничение области меняет поведение фильтра.
3. Test UI: точный Product COUNT через Test/Engagement JOIN ~404 ms в restricted-профиле; выборка страницы ~422 ms. Эти стоимости не являются N+1 только из-за числа запросов.
4. Dashboard: общая daily severity aggregation Round 5 уже используется один раз. Оставшаяся агрегация по миллиону findings ~307–557 ms SQL execute, ~317–617 ms в отдельных планах. Под конкуренцией конкурирует за CPU PostgreSQL.

## Решение для RC

Новых P2 performance-патчей: **0**. Сохранены все Round 1–5. Не добавлены индексы, cache, миграции и изменения сортировки/разрешений. Простой COUNT-патч не соответствует выявленному основному bottleneck. Следующий отдельный эксперимент: индекс для существующей сортировки на изолированной копии, оценка размера/стоимости insert/import, а также явная проверка tie-order и UI-фильтров. Индекс не создавался. До выбора стратегии title-фильтра необходимо сохранить его видимость и определить контракт лимита без порядка.

Полные SQL shapes, фактические планы, buffers и вложенные фазы: [ui-phases.json](measurements/ui-phases.json). Полные HTTP p50/p95/RPS из повторных прогонов приведены в PERFORMANCE.md. Необязательные stretch goals не объявляются достигнутыми.
