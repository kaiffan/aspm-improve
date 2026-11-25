# Регрессия безопасности

Финальный B с ASPM_TEST_API_ONLY=True дал **243 passed, 2 inherited skips, 0 failures, 0 errors** за 46,47 с. Выборка включала selection/ambiguity, coverage, idempotency, RBAC negatives, API-only ingestion, protected downloads, CSRF, Finding write races, deduplication и Product Stats/Metrics. Browser export по-прежнему проверяет Product edit. Чтение Commit выполняет исходный RBAC JOIN.

Предыдущие полные Django/JS и schema checks относятся к 12dfcbe. Для этой правки пройден целевой набор из десяти модулей. Изменены две Python точки read path. Миграции, write protocol и публичные параметры API сохранены.

[Машинный результат](raw/regressions.json)
