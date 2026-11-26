# 03 | Требования и ёмкость

Нужны Kubernetes согласно `kubeVersion` Chart (≥1.27), Helm, kubectl, Python ≥3.10 с PyYAML на машине оператора. TLS путь предполагает Ingress controller, доверенные сертификаты и рабочий DNS. Deploy запрашивает чтение Node, StorageClass, namespace и объектов выпуска, server dry run и создание временного диагностического Pod. Для Backup/Restore нужен совместимый PostgreSQL client.

| Профиль | Web / Worker / Beat | Concurrency | Django / nginx на Web, requests → limits | Worker на Pod, requests → limits | PostgreSQL |
|---|---:|---:|---|---|---|
| Local | 1 / 1 / 1 | 1 | 200m / 384Mi → 2 CPU / 2Gi; 50m / 64Mi → 500m / 256Mi | 250m / 512Mi → 2 CPU / 2Gi | Выделенная DB, лабораторные 100 серверных слотов |
| Standard HA | 2 / 3 / 1 | 2 | 600m / 1Gi → 1750m / 2Gi; 100m / 64Mi → 250m / 256Mi | 600m / 1Gi → 2 CPU / 2Gi | Расчёт 82 с ops и резервом. Старт отдельного сервера 100 |
| High Throughput | 2–3 / 3 / 1 | 2 | 750m / 1Gi → 1500m / 2Gi; 100m / 64Mi → 250m / 256Mi | 750m / 1Gi → 1500m / 2Gi | Расчёт 97. Worker HPA до 4, 104. Старт 120–128 |

Beat: 50m / 128Mi → 500m / 512Mi. Migration Job HA: 250m / 512Mi → 1 CPU / 2Gi. Standard steady-state requests около 3,25 CPU / 5,25 GiB, limits 10,5 CPU / 11 GiB. Во время rollout учитывайте `maxSurge: 1` для web и worker, длительный drain, terminating Pods, migration и preflight. High Throughput включает HPA web и требует resource metrics API.

Проектный бюджет приложения — 16 vCPU / 32 GiB. PostgreSQL, broker/cache, Keycloak, Ingress и мониторинг планируются отдельно. Для HA нужны два RWX PVC, место под наблюдения/артефакты и свободный резерв сверх `storage.minimumFreeBytes` (1 GiB). Ёмкость storage зависит от размера загрузок, количества версий и retention.

Лабораторный максимум PostgreSQL — 13 сессий на синтетических данных. Стартовый бюджет основан на процессах, потоках, rollout и отдельной квоте администрирования. [Измерения](../qualification/PERFORMANCE_REPORT.md)

Фактически использовано при лабораторной квалификации: Helm 4.2.0, OrbStack Kubernetes v1.36.5, Linux/ARM64, PostgreSQL 18.6, Valkey 9.1.2, Django 5.2.17, Python 3.14.8 и nginx 1.31.8. Варианты платформы заказчика проверяются отдельной установкой.
