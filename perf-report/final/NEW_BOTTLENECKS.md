# Newly discovered bottlenecks

Ранжирование после системного аудита: Simple Metrics (материализация и RAM), Products UI (дорогой SQL), Dashboard (повторная работа), затем Notes N+1 и оставшиеся exact counts/Findings UI. Выбраны три небольших исправления с подтверждённым HTTP-эффектом. Число SQL само по себе не равно стоимости: Products UI теперь делает дополнительный дешёвый агрегат и устраняет многократную дорогую работу.

Реестр [57 API registrations](routes.json) получен из Django router, маршруты не придуманы. Проверены основные API, users, product types, endpoints/status, notes, statistics и серверные страницы. Technologies и risk acceptance на этом наборе пусты; для production-нагрузки они не показательны. Reports преимущественно представлены действиями генерации и не запускались массово. Кастомные Engagements/SCM/HA/UI redesign не изменялись.

## Products UI

Три коррелированных finding count на продукт, включая повторный active count. Batch считает active/verified только для авторизованной страницы; count-сортировка сохраняет прежний SQL-путь.

- Files: `dojo/product/queries.py`, `dojo/product/ui/views.py`.
- CURRENT → FINAL p95: **2682.9 → 203.6 мс**; RPS **0.38 → 5.14**.
- SQL statements median: 38 → 39; SQL wall p50: 2577.6 → 163.1 мс.
- Порядок и границы страниц проверены; максимальный выигрыш показан для стандартной сортировки.

## Dashboard

Дневной GROUP BY выполнялся дважды: count и материализация. Месячная статистика вычисляла два EXTRACT на строку. Теперь дневные группы читаются один раз, месяц — TruncMonth.

- Files: `dojo/home/views.py`, `dojo/utils.py`.
- CURRENT → FINAL p95: **1364.6 → 962.5 мс**; RPS **0.76 → 1.08**.
- SQL statements median: 17 → 16; SQL wall p50: 1289.6 → 907.3 мс.
- Размер Python-результата зависит от числа дней/месяцев, а не числа findings; cutoff/unknown severity сохранены.

## Simple Metrics fresh render

Для вычисления чисел загружались все Finding-поля и Python-списки, особенно len(closed). Теперь severity counts и exact closed count вычисляет PostgreSQL.

- Files: `dojo/metrics/views.py`.
- CURRENT → FINAL p95: **4293.0 → 1226.4 мс**; RPS **0.24 → 0.84**.
- SQL statements median: 16 → 16; SQL wall p50: 1404.1 → 1175.4 мс.
- Авторизованные Product Types и все фильтры сохранены; cache hit измеряется отдельно.

## SQL and EXPLAIN evidence

Фактический SQL и `EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)` безопасных SELECT сохранены:

- [ORIGINAL](explain_original.json), [CURRENT](explain_current.json), [FINAL](explain_final.json).
- [Original Products API](explain_extra_original.json), [Current Products API](explain_extra_current.json), [Final Products API](explain_extra_final.json).
- [Диагностика всей системы](audit_current.json), [SQL audit](audit_sql.jsonl), [альтернативные планы](plan_trials.jsonl).

SQL params не записывались, строковые literals в SQL замаскированы. Execution Time EXPLAIN и SQL wall time HTTP — разные измерения. Shared reads означают загрузку в PostgreSQL shared buffers; при выключенном track_io_timing они не доказывают физическое чтение SSD.

## Ограничения и отклонённые кандидаты

Notes list выполняет запрос history на строки; на текущем маленьком наборе это около 22 SQL и единицы миллисекунд, поэтому патч не оставлен. Обычные Tests/Engagements не показали значимого нового N+1 на этом датасете. Findings UI/Test UI, точный COUNT и большие Product ID arrays остаются дорогими. В оставшихся Dashboard counters широкие DISTINCT-проекции сопровождаются большими temp spills; сокращение проекции до PK — кандидат следующего раунда с отдельной проверкой семантики. Добавление индексов или настройка сервера без отдельного доказательства не выполнялись.

В диагностике обнаружены два источника ложного сравнения: общий page cache разных сборок и отсутствие column statistics в первых write-копиях. Финальные серии используют отдельные namespaces и копии после ANALYZE. Старые данные сохранены в `cache_shared_diagnostics/` и `background_unanalyzed/` и не включены в итоговые метрики.
