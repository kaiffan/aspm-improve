# 07 | Хранилище

Provision два PVC в namespace. `storage.existingClaim` монтируется как private evidence, `storage.mediaExistingClaim` как media. Для HA оба должны иметь ReadWriteMany. Приложение запускается от UID 1001/GID 1337 с fsGroup 1337. Подготовьте права средствами CSI/владельца томов. Private evidence оставляйте на закрытом storage.

Проверьте запись в preflight, `fsync`, atomic rename, read-after-write и SHA-256 оригинала с двух реплик. Настройте byte/inode alarms. Согласуйте snapshots, шифрование, retention и RPO/RTO. `storage.minimumFreeBytes` по умолчанию 1073741824. Нехватка резерва блокирует старт и загрузки. Local использует RWO на одном узле. Для HA проверьте отказ узла и republish на корпоративном CSI.
