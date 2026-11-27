# Квалификация S3

MinIO собран из закреплённого исходного релиза и запущен в новом локальном Compose-проекте. Клиент проверял TLS по лабораторной CA. Создан отдельный versioned bucket. Тесты повторены на финальном runtime c95177336f4d92580bf463e11d3d129490aba88c. 9 тестов за 12.234 с · OK. Обнаружено по группам: 9. [Исходный релиз MinIO](https://github.com/minio/minio/releases/tag/RELEASE.2025-10-15T17-29-55Z).

Проверены version pinning, checksum, повторная доставка, условная публикация отчёта, 48 MiB multipart, abort, временная недоступность, Classic media и возобновляемый перенос filesystem → S3. Доказательства — s3-bootstrap.log и s3-tests.log. Сетевые отказы корпоративного S3, SSE/KMS и полноценный restore versioned bucket в новом Kubernetes namespace остаются NOT TESTED.
