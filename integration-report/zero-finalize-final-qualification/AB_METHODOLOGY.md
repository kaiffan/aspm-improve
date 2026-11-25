# Методика полного A/B

A = 19cd7b4129de52e75eabaf0e07739e4c2b682f8e. B = 25da29aaff229d3a815e223d8af8bdc4ecca7c5e. Разница B относительно первого Zero-Finalize ограничена двумя файлами read path. Native build фиксирует Git revisions, OCI labels, архитектуру, Git blobs и проверяет одинаковый inventory Python packages.

Один изолированный PostgreSQL 18.6, общий запечатанный 1M dump и одна чистая копия на независимый повтор. Перед нагрузкой проверяется fingerprint восстановленных строк. Повторы чередуются A1, B1, B2, A2, A3, B3. Приватный Valkey/cache создаётся заново. Credentials, memberships, browser sessions, workers, quotas, fixtures и наблюдение одинаковы. Оба варианта прогреваются. Наборы сырых данных именуются по семейству, варианту и повтору.

Каждый Core9 point сохраняет 300 запросов, p50/p90/p95/p99, RPS, ошибки, SQL count/time, статистику PostgreSQL по планированию и выполнению, CPU и I/O. Acceptance сохраняет 400 проверенных business operations. Scanner load запускается отдельно. При устойчивом росте хвоста разбирать маршрут, SQL time, saturation и очередь. Локальные диагностические числа и старые прогоны других SHA не входят в эти результаты.

[Зафиксированный план](raw/native-campaign-plan.json) · [Входные workload hashes](native/workload-lock.json)
