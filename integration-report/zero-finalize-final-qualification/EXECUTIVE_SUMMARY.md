# Финальная проверка Zero-Finalize

Локально подтверждены функциональность, оптимизация Overview и восстановление импорта. Релизная performance-квалификация остаётся **HOLD**. Доступной native AMD64/Ryzen VM не найдено. Для полного 1M A/B на Mac не хватает свободного места.

- Overview перешёл с 13 запросов в A на 23 в исходном B. Точечная правка сократила B до 18, либо до 13 при неоднозначном pipeline. Число SQL стабильно при 1–1 000 ScanRuns. Работа PostgreSQL внутри запросов растёт с количеством строк.
- Строгая регрессия финального B дала 243 passed и два унаследованных skip. Проверены конкурирующие PATCH и reimport, deduplication, Product Stats/Metrics и RBAC.
- Три параллельных scanner reports завершились за 0,62 с. Пачка 100 заданий по десяти репозиториям завершилась за 6,13 с. Старый экспорт сохранил хэши. Broker outage и SIGKILL worker восстановились через outbox.
- Пробный dump/restore на малой базе сохранил четыре fingerprints. Read-only проверка защищённого 1M seed подтвердила исходный SHA-256.
- Для Ryzen собран комплект сборки, Compose, восстановления, нагрузки и сбора метрик. Локально проверены хэши входов, Python/JS-синтаксис, build/campaign plan и Compose config.

[SQL](OVERVIEW_SQL_ANALYSIS.md) · [Нагрузка](ZERO_FINALIZE_LOAD.md) · [Развёртывание](RYZEN_DEPLOYMENT.md) · [Решение](RELEASE_GATE.md)
