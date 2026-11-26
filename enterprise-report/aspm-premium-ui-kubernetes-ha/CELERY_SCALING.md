# Celery и outbox

Три worker pod обслуживают очередь celery. В стандартном HA два prefork child на pod, в OrbStack один. Prefetch равен 1. HA readiness использует адресный Celery ping. Grace 960 секунд превышает hard limit ingestion 900 секунд. Worker HPA опционален. Критические очереди остаются взаимозаменяемыми между всеми worker.

Beat имеет Recreate и PostgreSQL advisory lock. Dispatchers забирают jobs через SKIP LOCKED. Для каждой scan/report задачи используется session advisory lock. Late ACK, reject-on-worker-lost и периодический outbox позволяют повторить незавершённую обработку. Эксперимент прерывает только подтверждённый дочерний процесс синтетического ScanRun и сверяет один наблюдаемый результат и прежний Test.

[Прерывание](raw/worker-interruption.txt) · [Лог](raw/worker-task-events.txt) · [Результат](raw/ingestion-recovery.json)
