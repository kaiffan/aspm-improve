# Миграции и DB guards

Модели ScanRun/FindingObservation/CommitScanSet/GeneratedReport/IngestionJob не изменены. Миграция 0316 и FK-backed immutable membership сохранены byte-for-byte. Новая миграция не требуется.

Свежие runtime/test базы применили всю цепочку до 0316. `makemigrations --check --dry-run`: **No changes detected**. Django system check: 0 errors; dev/test image предупреждает о components/node_modules (staticfiles.W004). Обе OpenAPI schemas валидны.

Тесты проверили запрет rewrite/delete finalized memberships, completed scans/observations/reports, source relationships и межпроектных связей. Report generation использует только manifest, не live selection. Никаких data rewrite старых GeneratedReport, observations или source artifacts при переходе не выполняется.

Metadata lock для Development environment не меняет schema и не удаляет существующие дубли: выбирается первая existing запись. [Source fingerprints](protected-source-fingerprints.json), [drift log](logs/migration-drift.log.gz).
