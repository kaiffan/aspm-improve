# Disaster recovery

Созданы PostgreSQL custom dump и tar приватных файлов синтетической Compose установки. Проверены SHA-256 обоих файлов. Восстановление выполнено в новую пустую базу aspm_final_restore одной транзакцией. Исходную базу сохранили. Получено совпадение упорядоченной выборки ScanRun и 8 оригиналов. Время pg_restore — 2 с. Это измерение на малом dataset.

Живой запуск восстановленного release в отдельном Kubernetes namespace, восстановление S3 versions, Keycloak, webhook receiver и pending jobs остаются NOT TESTED. Подтверждённого production RPO/RTO нет.
