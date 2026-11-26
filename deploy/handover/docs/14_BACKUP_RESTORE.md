# 14 | Резервное копирование и восстановление

1. Владелец согласует RPO/RTO, полноту PostgreSQL/PVC snapshots и encryption. Для согласованной точки восстановления остановите внешние записи, дождитесь outbox и активных worker задач, зафиксируйте время. Снимите согласованные копии DB, private evidence и media. Secret manager отвечает за ключи шифрования, CA и ссылки. Восстановление требует исходный AES ключ для уже зашифрованных настроек.
2. Подготовьте libpq service entries для источника и выделенной цели, `PGSERVICEFILE` и защищённый `PGPASSFILE` (0600). Используйте `sslmode=verify-full` на внешней инфраструктуре. PostgreSQL client должен поддерживать версию источника.
3. Dump и verify в защищённом каталоге. Сохраните checksum вместе с dump и идентификатором snapshot обоих PVC.

```bash
scripts/backup.sh aspm-backup aspm /secure/backups/aspm.dump
scripts/restore.sh aspm-rehearsal aspm_restore /secure/backups/aspm.dump aspm aspm-rehearsal/aspm_restore
```

Restore требует отдельную пустую БД и подтверждение имени. Выделите независимые тома и endpoints для стенда. Сверьте migration plan, счётчики объектов, SHA-256 артефактов, восстановленный отчёт, login и RBAC, затем проведите smoke на восстановленной системе. Восстановление боевой БД и возврат трафика — отдельное решение DBA/SRE по утверждённому плану.
