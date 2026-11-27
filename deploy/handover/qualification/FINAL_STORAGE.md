# Квалификация S3 и восстановления | Helm 0.1.0-rc.11

Код кандидата зафиксирован в `ff30da23b3` на ветке `feature/aspm-final-reliability-ux-storage`. Предыдущий проверенный кандидат `77a6b79a2e` объединяет Enterprise Delivery и Monitoring, содержит `origin/dev` и SHA из брифа. Его rollback ref — `aspm-1.0.1-rollback-rc10`. Базовый образ Monitoring проверялся на `a4fb9e89926f`. Тестовый ARM64 Django-кандидат собран из исходников ветки поверх этого образа и установлен с прежним nginx.

| Проверка | Результат |
|---|---|
| Django | 35 регрессионных тестов файлового профиля и SSO/RBAC. Проверены миграции и OpenAPI |
| S3 contract | 9 тестов с versioned Moto по HTTPS и отдельной CA. Условная запись, pinned version, ошибка при потере версии, 48 MiB, HTML/JSON более 32 MiB, прерванный multipart, обе части отчёта, Classic media, повтор outbox и возобновляемый перенос filesystem → S3 |
| Compose HTTP | Три одновременные загрузки, включая 50 331 648 байт. Повтор той же доставки HTTP 200, cross-Product download HTTP 404, сверены исходные SHA-256 и оба формата отчёта. Проверены Scan Processing, System Health и Reports |
| Helm | 23 проверки рендера. Helm HTTP smoke пройден в отдельном namespace. После восстановления узла запущены 2 web, 3 worker и 1 Beat. Единственный PVC тестового S3-профиля использовался локальной PostgreSQL |
| Disaster Recovery | Согласованы PostgreSQL dump, deployment description и контрольные суммы файлов. В новом Kubernetes namespace восстановлены пустая БД и 10 файлов в другой S3 bucket/prefix. Проверены SHA-256, Classic-вложение и завершение восстановленного pending ScanRun. REST после восстановления выдал три исходных файла и оба формата отчёта |
| Chromium | Scan Processing, System Health и Reports проверены при 1440 и 390 пикселях с доступной таблицей и без переполнения страницы |
| Ограничение стенда | Один узел OrbStack ARM64. При наложении Compose и Helm нагрузок наблюдались OOM-перезапуски, включая локальную PostgreSQL. Второй Helm rollout на восстановленную БД остановился на Pending migration Job из-за нехватки памяти. HTTP после восстановления сверили отдельным процессом Django в том же namespace |

## Открытые проверки

- Корпоративный S3-провайдер, TLS chain, IAM, SSE/KMS, ротация credentials, Object Lock при необходимости и lifecycle неполных multipart.
- Миграция конкретного RWX CSI и существующего набора файлов в корпоративное хранилище, аварийный rollback после возобновления writes.
- Стабильный повторный rollout Helm на восстановленную БД. Выделенный multi-node Kubernetes, длительная нагрузка и сетевые отказы PostgreSQL, Valkey, Keycloak и S3. Native Linux/AMD64 release images и их security scan.
- Корпоративные Keycloak/AD, Prometheus, VictoriaMetrics, Grafana, Alertmanager и реальные роли/отзыв групп. Доказательства интеграции rc.10 сохранены как исторические.
- DBA PITR, корпоративное резервное хранилище вне runtime bucket, секреты и измерение RPO/RTO.
- Полная готовность к производственной эксплуатации остаётся **HOLD**.

[Инвентаризация](../docs/STORAGE_INVENTORY.md) · [Миграция](../docs/19_S3_STORAGE_AND_CUTOVER.md) · [Восстановление](../docs/14_BACKUP_RESTORE.md)
