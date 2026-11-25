# Очередь Celery и восстановление

| 100 независимых заданий | p50 | p95 |
|---|---:|---:|
| Acceptance timestamp → worker start | 2 327 мс | 4 033 мс |
| Worker start → persisted completion | 48 мс | 106 мс |
| Acceptance timestamp → persisted completion | 2 374 мс | 4 076 мс |

Основное время в burst уходит на очередь. Штатные задания завершились. Один FAILED вызван намеренно невалидным payload для mixed-state сценария.

POST при остановленном broker оставил ACCEPTED и outbox. После старта broker тот же scan завершился с одним observation и без оставшегося outbox. SIGKILL в PROCESSING оставил тот же Test и outbox. Повторная доставка завершила attempt 2 с ровно 3 000 видимых observations в generation 2 и тем же Test. Таймер повторной отправки приближен только для двух synthetic jobs, штатная задержка Beat здесь не измерялась.

[Сырые timestamps](raw/zero-finalize-load.json) · [Доказательство восстановления](raw/worker-faults.json)
