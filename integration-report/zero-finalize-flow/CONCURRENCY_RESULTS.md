# Конкурентная корректность

[Фактические 10 проверок](checks/concurrency-green.json), [реальные worker/broker faults](checks/worker-faults.json), [HTTP flow из собранного image](checks/image-http-smoke.json).

| Сценарий | Результат |
|---|---|
| Два scanners одновременно на Commit | 202 для обоих, общий Commit, отдельные ScanRuns/Tests |
| Два runs одного scanner | Отдельная история; live выбирает один по scanner/scope/attempt policy |
| Четыре одинаковые доставки | Один 202, три 200, один ScanRun/outbox |
| Один key с другим содержимым | 409 |
| Два отчёта одновременно | Разные последовательные versions 1 и 2 |
| Upload во время export | Pending run не включён; membership/manifest/JSON содержат один и тот же frozen набор |
| Поздний COMPLETED | Live изменяется; старые HTML/JSON/checksums остаются прежними |
| FAILED при чтении | Видим в history и status API |
| Duplicate worker delivery | Один import attempt |
| Broker dispatch exception | Outbox сохраняется, повторная доставка завершается |
| Настоящая остановка broker | POST вернул ACCEPTED; durable outbox восстановил COMPLETED после запуска broker |
| SIGKILL worker во время импорта | PROCESSING + outbox сохранились; после restart attempt 2 / generation 2, тот же Test 14, 3000 observations |
| PATCH Finding / reimport / concurrent delete | Соответствующие RC5 oracles прошли внутри полного suite |

Для fault tests используются только собственные containers. Dispatcher retry time ускорялся только у двух synthetic jobs; импорт и восстановление выполнял настоящий Celery worker. Новых retry/outbox протоколов не введено.

До fix реальные parallel imports создали две Development environment записи, после чего следующий import упал с MultipleObjectsReturned. После короткой metadata lock + deterministic existing-row selection все проверки прошли, включая новый behavioral regression test для существующих дублей. Locks не охватывают parsing/Finding processing.
