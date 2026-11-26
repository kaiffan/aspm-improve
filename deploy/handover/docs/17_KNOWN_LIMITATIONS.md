# 17 | Известные ограничения

- На OrbStack один узел. RWO, лабораторные зависимости и pod-level recovery покрывают только локальную топологию.
- Corporate registry, AMD64, Keycloak/AD, external DB/CSI failover, production-like нагрузка и RPO/RTO имеют отдельные gates.
- Время приёма и завершения сканов зависит от CPU throttling, размера отчёта, очереди, PostgreSQL, сетевой цепочки и latency storage.
- Корпоративное обозначение FF остаётся UNCONFIRMED до получения названия и очищенного примера.
- Оценки 1–20 млн Findings требуют отдельного стенда и воспроизводимого нагрузочного профиля.
- Security supply chain имеет отдельные findings и действия. [Отчёт](../qualification/SECURITY_REPORT.md)
- Тестирование интерфейса покрывает указанные браузер, размеры и сценарии. [Матрица](../qualification/TEST_MATRIX.md)
