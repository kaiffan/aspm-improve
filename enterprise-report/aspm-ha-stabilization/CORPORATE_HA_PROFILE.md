# Корпоративный профиль ASPM

Кандидат Helm `0.1.0-rc.8`. Основной профиль `values-ha.yaml` плюс `values-production.example.yaml` и приватный overlay площадки. Последний файл задаёт собственные DNS, registry digests, Secret/PVC и NetworkPolicy. Внешние PostgreSQL, broker/cache, Keycloak, хранилище и контроллер ingress предоставляет площадка. В лаборатории они проверялись на OrbStack и в отдельном тестовом контуре Keycloak.

[Helm: HA](../../deploy/helm/aspm/values-ha.yaml) · [Helm: High Throughput](../../deploy/helm/aspm/values-high-throughput.yaml) · [Helm: Production example](../../deploy/helm/aspm/values-production.example.yaml) · [Helm: внешний PostgreSQL](../../deploy/helm/aspm/values-external-postgresql.example.yaml) · [Helm: OrbStack](../../deploy/labs/orbstack/values-ha.yaml) · [Упакованный RC](raw/aspm-0.1.0-rc.8.tgz)

| Входные данные | Что согласовать с владельцем площадки | Ключи чарта и Secret |
|---|---|---|
| Образы | Django и nginx одной сборки, registry, доверенный digest каждого целевого manifest и архитектуры, pull credential | `image.repository`, `image.digest`, `nginxImage.repository`, `nginxImage.digest`, `imagePullSecrets` |
| Django | Общий секрет подписи приложения и ключ шифрования сохранённых интеграций. Нужны всем репликам и для восстановления | `existingSecret`, `secretKeys.secretKey` → `django-secret-key`, `secretKeys.credentialKey` → `credential-aes-key` |
| PostgreSQL | Версия, primary/failover endpoint, DNS/порт, database/schema, пользователь, способ выдачи пароля, роли миграций, trust chain, CIDR, квота соединений и RPO/RTO | `secretKeys.databaseUrl` → `database-url`, `databaseTLS.existingSecret`/ `ca.crt`, `config.DD_DATABASE_OPTIONS` с `sslmode=verify-full`, `config.DD_DATABASE_CONN_MAX_AGE` |
| Broker | Собственный Redis/Valkey HA endpoint, ACL, TLS trust, persistent queue/replication policy, no eviction, порт и предел соединений. Проверить failover через фактический client URL и подтверждения Celery | `secretKeys.brokerUrl` → `broker-url`, `networkPolicy.egress` |
| Cache | Отдельный HA endpoint и ACL/credential, TLS trust, memory, eviction и failover. Все веб-реплики должны обращаться к общему cache | `secretKeys.cacheUrl` → `cache-url`, `networkPolicy.egress` |
| Keycloak | Публичный HTTPS realm issuer, confidential client, exact callback и logout redirect, `client_secret_basic`, role claim и scoped product grants, срок сессии и обновления grants, private CA по необходимости | `oidc.enabled`, `issuer`, `callbackUrl`, `clientId`, `clientAuth`, `existingSecret`, `clientSecretKey`, `existingCaSecret`, `roleClaim`, `groupClaim`, `secopsRole`, `expertRole`, `userRole`, `sessionAge`, `groupTtl`, `providerLogout` |
| RWX | Два существующих PVC в namespace релиза, StorageClass/CSI, размер, snapshot, право на mount из нескольких зон, UID 1001 / GID 1337, rename и fsync из разных pod. Артефакты и отчёты хранятся в приватном volume | `storage.existingClaim`, `storage.mediaExistingClaim`, `storage.minimumFreeBytes`, `podSecurityContext`, `config.DD_ASPM_ARTIFACT_ROOT` |
| Ingress | DNS/web origin, ingress class и namespace, сертификат и ротация, forwarded proto от доверенного прокси, body limit и тайм-ауты под размер скана и отчёта, backend draining, health и отсутствие callback query strings в логах | `ingress.className`, `host`, `tlsSecretName`, `annotations`, `config.DD_SITE_URL`, `DD_ALLOWED_HOSTS`, `DD_SESSION_COOKIE_SECURE`, `DD_CSRF_COOKIE_SECURE`, `DD_SECURE_PROXY_SSL_HEADER` |
| NetworkPolicy и monitoring | Рабочий CNI, разрешённые PostgreSQL, broker, cache, issuer и webhook получатели, DNS. Метрики на 8081, ServiceMonitor CRD, namespace/pod selector для Prometheus, owner alert routing | `networkPolicy.ingressNamespace`, `ingressPodSelector`, `egress`, `monitoring.serviceMonitor`, `config.DD_DJANGO_METRICS_ENABLED` |

## Реплики и ресурсы

| Компонент | Steady | Requests на pod | Limits на pod для Standard |
|---|---:|---|---|
| Django | 2, на pod 2 процесса × 2 потока | 600m CPU / 1 GiB | 1750m CPU / 2 GiB, при пиковой нагрузке 2 CPU |
| nginx, sidecar Django | 2 | 100m / 64 MiB | 250m / 256 MiB |
| Worker | 3, на pod concurrency 2 | 600m / 1 GiB | 2 CPU / 2 GiB |
| Beat | 1 | 50m / 128 MiB | 500m / 512 MiB |
| Migration Job | до 1 активного Job на релиз | 250m / 512 MiB | 1 CPU / 2 GiB |

Standard в установившемся режиме суммарно запрашивает 3,25 CPU и 5,25 GiB. Лимиты суммарно 10,5 CPU и 11 GiB. Overlay с 2 CPU Django доводит суммарный CPU limit до 11 CPU. Для одного web surge и одного worker surge одновременно добавьте 1,3 CPU и 2,0625 GiB по requests. При расчёте полной ёмкости добавьте команды миграции, ещё живые pod в Terminating и системную нагрузку. Deployment использует `maxUnavailable=0` и `maxSurge=1` для каждого из web и worker. Работоспособность autoscaling требует свободной ёмкости узлов, CPU requests, metrics-server и проверенной задержки в очереди. Для High Throughput chart включает web HPA на 2–3, настройка HPA для worker 3–4 предусмотрена и по умолчанию выключена. У профиля High Throughput 1,5 CPU на Django и worker. Для частых bursts сначала повторите приёмо-сдаточный замер с этой ёмкостью или передайте overlay с 2 CPU Django.

`web.replicas` и `worker.replicas` задаются независимо, HPA может управлять их количеством. Beat отключается `beat.enabled` и при включении имеет ровно один pod, Recreate и session-level fencing. Управление параллельными планировщиками несовместимо с безопасной схемой релиза. Standard использует PDB 1 из 2 для web и 2 из 3 для worker. На нескольких узлах он применяет topology spread по hostname с `DoNotSchedule`, предпочтительную anti-affinity по компоненту и spread по зонам с `ScheduleAnyway`. Правила зависят от labels и ёмкости реальных узлов. PDB регулируют добровольные disruptions и не заменяют ресурсный резерв или readiness.

## Эксплуатация и оставшиеся условия

До production нужны утверждённые внешние endpoint и параметры из таблицы, совместимый CNI и CSI, проверка PostgreSQL и Redis/Valkey failover с реальными driver URL, доступность Keycloak, корпоративная маршрутизация/TLS, мониторинг и журналирование доступа. Настройте сигналы readiness и rollouts, HTTP 5xx и TCP, acceptance p95, CPU throttling, отставание outbox, очередь и worker recovery, retries/DLQ webhook, connections и lock waits PostgreSQL, заполняемость и latency RWX. При резервном копировании согласуйте точку PostgreSQL/PITR с evidence и media snapshots, отдельно храните Secret и ключи. Подтвердите в новом namespace восстановление того же SHA, миграции, количество записей и SHA-256 оригиналов с обеих реплик, зафиксируйте RPO/RTO. Предыдущая проверка PostgreSQL 18.6 восстановила маленький синтетический архив с совпавшими контрольной суммой и числом продуктов, Findings, ScanRuns, Observations и GeneratedReports.

OrbStack имеет один узел, по одной реплике PostgreSQL, broker, cache и Traefik, а также локальное RWX. Node failure, фактическая топология доменов отказа, корпоративные RPO/RTO и работа под большим датасетом требуют согласованной площадки. Production HOLD. Stable не опубликован.

[Предыдущая проверка restore](../aspm-premium-ui-kubernetes-ha/raw/backup-restore.txt) · [Шаблоны Deployment](../../deploy/helm/aspm/templates/workloads.yaml) · [Шаблоны HPA/PDB](../../deploy/helm/aspm/templates/scaling.yaml) · [Бюджет PostgreSQL](POSTGRESQL_CONNECTION_BUDGET.md)
