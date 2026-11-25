# Реальная нагрузка Zero-Finalize

Локальный ARM64 image B, PostgreSQL 18.6, два Celery prefork workers и отдельный Valkey. Только синтетические данные. Шесть записей ресурсов охватывают 17,79 с. p50/p95 по HTTP POST с 202 составили 166,05 / 212,82 мс.

| Сценарий | Фактический результат |
|---|---|
| Semgrep → Trivy → Gitleaks | 1,64 с с проверкой видимости каждого ScanRun и его findings |
| Три scanner одновременно | 0,62 с, один Commit, три ScanRuns, 1 / 5 / 1 finding. Replay вернул прежний ID, конфликтующий payload дал 409 |
| 100 jobs × 10 repositories | 6,13 с, десять upload clients и 100 уникальных COMPLETED ScanRuns с одним finding на каждый |
| Длинная история | 1 000 ScanRuns, отдельно измерены Overview, Scanner Reports, Findings и Compare |
| Report freeze и поздний upload | 2,26 с с проверками. Три уникальных ScanRun в membership. SHA-256 JSON и HTML совпали до и после завершения позднего отчёта |
| Broker/worker fault | Настоящая остановка broker и SIGKILL worker с восстановлением |
| Смешанные состояния | Одновременно COMPLETED, PROCESSING, FAILED. Coverage INCOMPLETE. Незавершённый scan не включён в успешные результаты |
| Большой отчёт | 1 500 реальных observations за 6,99 с с подготовкой смешанных состояний. Отдельный rollback fixture на 10 000 observations для UI |

Сначала лаборатория унаследовала DNS alias соседнего broker. Accepted запись сохранилась в outbox и обработалась после выделения отдельного alias. Таблица показывает повтор с изолированной очередью. Время сценариев включает проверки и polling.

[События](raw/zero-finalize-load.json) · [Ресурсы](raw/zero-finalize-metrics.json) · [Очередь](CELERY_QUEUE_ANALYSIS.md)
