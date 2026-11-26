# Совместимость Classic и DevSecOps

Projects отображает Product. Задачи DevSecOps идут через Repository, Commit и ScanRun к исходному scanner report или версионированному ASPM export. Classic сохраняет Product Type, Product, Engagement, Test, Finding и Reports. Scanner Reports с фактической связью ведёт к Test и Engagement. Из Projects доступны оба рабочих маршрута.

Карточка коммита сохраняет выбор пайплайна, immutable export, исторические observations и сравнение. ACCEPTED, PROCESSING, COMPLETED и FAILED остаются отдельными статусами. Внешние сканеры используют API-only ingestion. Classic import/reimport принимает сценарии без Git. Оба маршрута используют существующий RBAC.

[Строгие тесты](REGRESSION_RESULTS.md) · [Zero-Finalize](raw/ingestion-recovery.json)
