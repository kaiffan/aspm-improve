# 14 | Резервное копирование и восстановление

1. Владелец согласует RPO/RTO, полноту PostgreSQL/PVC snapshots и encryption. Для согласованной точки восстановления остановите внешние записи, дождитесь outbox и активных worker задач, зафиксируйте время. Снимите согласованные копии DB, private evidence и media. Secret manager отвечает за ключи шифрования, CA и ссылки. Восстановление требует исходный AES ключ для уже зашифрованных настроек.
2. Подготовьте libpq service entries для источника и выделенной цели, `PGSERVICEFILE` и защищённый `PGPASSFILE` (0600). Используйте `sslmode=verify-full` на внешней инфраструктуре. PostgreSQL client должен поддерживать версию источника.
3. Dump и verify в защищённом каталоге. Сохраните checksum вместе с dump и идентификатором snapshot обоих PVC.

```bash
scripts/backup.sh aspm-backup aspm /secure/backups/aspm.dump
scripts/restore.sh aspm-rehearsal aspm_restore /secure/backups/aspm.dump aspm aspm-rehearsal/aspm_restore
```

Restore требует отдельную пустую БД и подтверждение имени. Выделите независимые тома и endpoints для стенда. Сверьте migration plan, счётчики объектов, SHA-256 артефактов, восстановленный отчёт, login и RBAC, затем проведите smoke на восстановленной системе. Восстановление боевой БД и возврат трафика — отдельное решение DBA/SRE по утверждённому плану.

## Согласованная копия базы и файлов для S3

Проводите backup во время общего окна остановки записей. Отключите входящие изменения, приостановите Beat, дождитесь активных задач и остановите web и worker. Проверьте, что внешние jobs и администраторы также остановили записи. Оставшиеся pending ScanRun и outbox сохраняются в дампе PostgreSQL. Изменения Keycloak, если они включены в тот же recovery point, координируйте с владельцем identity infrastructure.

Используйте новый каталог с правами `0700`. На один recovery point нужны:

- `database.dump` и его SHA-256 из `scripts/backup.sh`. Дамп содержит Product grants/Keycloak mappings приложения, политики Engagement, настройки webhook, ScanRun и outbox. Для PITR попросите DBA зафиксировать timestamp/LSN и retention WAL, соответствующие окну остановки.
- `storage/objects.jsonl` и файлы из `python manage.py aspm_storage_transfer export --writers-paused --directory <new-directory>/storage`. Export читает сохранённые версии S3, проверяет байты и включает scanner artifacts, generated reports и Classic evidence/media.
- `deployment.json` с версиями Helm/image digests, экспортом настроек без секретов, именами и ревизиями Secret в защищённом хранилище, настройками Keycloak, namespace/Ingress/CA и параметрами PostgreSQL/S3. Если архив содержит шифротекст webhook, для расшифровки нужен соответствующий ключ ASPM. Список Secret и доступ к ним восстанавливаются через отдельно утверждённое хранилище.
- `RECOVERY_MANIFEST.json`, созданный командой `python scripts/recovery-manifest.py seal <new-directory> --writers-paused --application-sha <sha> --chart-version <chart> --source-database <database>`. Команда сверяет каждый blob с реестром, хеширует дамп, конфигурацию и реестр. Проверьте копию после переноса и храните манифест с копией в отдельном защищённом backup storage с собственным IAM и retention.

Для восстановления в новый namespace подготовьте отдельную PostgreSQL, S3 bucket или отдельный префикс, Keycloak/Ingress и runtime Secret. Web, worker и Beat остаются выключены. Выполните `python scripts/recovery-manifest.py verify <directory>`, затем `scripts/restore.sh` для пустой PostgreSQL. В maintenance pod с образом кандидата и S3-профилем целевого namespace выполните:

```bash
python manage.py aspm_storage_transfer restore --writers-paused \
  --directory /restore/storage --confirm-target TARGET_DATABASE \
  --expected-inventory-sha256 INVENTORY_SHA256
```

Для переноса в новый bucket или префикс утилита записывает объект под тем же логическим именем и идентичностью, проверяет SHA-256 и заменяет в целевой базе VersionId и расположение на фактические. Исходные версии сохраняются в backup и исходном bucket. Проверьте оба формата generated report, исходные сканы, Classic вложения и разграничение доступа до открытия трафика. Сначала запустите web и worker при изолированных внешних интеграциях. Проверьте pending ScanRun и состояние webhook (живые callback могут повторно отправить исторические доставки), затем включите Beat и ingress. Зафиксируйте фактические RPO/RTO и проверьте обратимость до объявления восстановления завершённым.
