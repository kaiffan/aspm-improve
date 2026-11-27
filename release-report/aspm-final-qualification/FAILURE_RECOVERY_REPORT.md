# Отказы и восстановление

| Сценарий | Наблюдение | Статус |
|---|---|---|
| Невалидный private root | HTTP 500 и HTTP 400 до правки. Добавлены два регрессионных сценария | Повтор на финальной ревизии в FINAL_REGRESSION |
| PostgreSQL после OOM | Первая попытка preflight завершилась OperationalError. После восстановления preflight прошёл | Наблюдение в OrbStack |
| PostgreSQL в миграции | Вторая миграция остановилась на database system is in recovery mode. Третья достигла запуска workloads | PASS для последующей миграции |
| Очередь во время остановки worker | ACCEPTED → COMPLETED. 8973 мс до завершения. Сверены один Finding и SHA-256 | PASS в Compose |
| Broker, cache, Beat | OOM, retries readiness, workload rollout не завершён | FAIL в лаборатории |
| S3 временно недоступно | Отдельный MinIO suite проверял отказ и возобновление outbox | PASS в ограниченном тесте |
| Продолжение сессии между web replicas, остановка IdP, replay webhook, remote_write outage | Контролируемый сценарий ещё не выполнен | NOT TESTED |

Ошибки клиента и число lost/duplicate tasks под load во время pod replacement на финальном SHA не измерены.
