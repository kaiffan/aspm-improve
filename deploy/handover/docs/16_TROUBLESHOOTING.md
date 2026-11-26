# 16 | Эксплуатационный runbook

Работайте с явно выбранными context, namespace и release. Снимите время начала, correlation ID, статус Helm и последние события. Перед эскалацией удалите из диагностических материалов токены, cookies и данные клиентов.

```bash
k() { kubectl --context "$ASPM_CONTEXT" -n "$ASPM_NAMESPACE" "$@"; }
k get deployments,pods,jobs,pvc,svc,endpointslice
k get events --sort-by=.lastTimestamp
helm history aspm --kube-context "$ASPM_CONTEXT" -n "$ASPM_NAMESPACE"
```

| Симптом | Безопасная диагностика и нормальный результат | Восстановление, проверка и эскалация |
|---|---|---|
| Web CrashLoopBackOff | `k describe pod WEB`, `k logs WEB -c web --previous`, `k logs WEB -c schema-and-storage`. Init успешно завершается | Проверьте миграции, mount, memory и образ. Исправьте с помощью reviewed values, дождитесь Ready. SRE при повторении |
| Migration Job FAILED | `k describe job JOB`, `k logs job/JOB`. Сверьте план и номер миграции | DBA проверяет блокировки, роль и backup. Повторите upgrade после устранения причины. Не запускайте параллельные миграции |
| DB connection refused | Preflight из namespace. DNS и SQL SELECT 1 успешны | Восстановите primary/route или Secret reference. При failover DBA подтверждает endpoint, сессии и queue recovery |
| PostgreSQL TLS failure | `pg_stat_ssl` из verify-full соединения. Проверьте hostname/CA/expiry | DBA обновляет CA и URI без ослабления verification. Повторите preflight |
| Keycloak login failure | Issuer discovery, IAM logs, TLS, время. Issuer совпадает буквально | IAM восстанавливает IdP/AD и client. Повторите вход и выход тестовым аккаунтом |
| OIDC callback error | Проверьте `oidc.callbackUrl`, зарегистрированный redirect, session cookie и IdP event | IAM/SRE исправляют FQDN/proxy/client, тестируют новый flow на чистой сессии |
| User не видит Project | Access Management, доверенные claims и project ID, TTL. Сравните Classic и DevSecOps | IAM проверяет grants, перезапускает вход или ждёт TTL. Проверьте соседний проект с отдельной учётной записью |
| Worker без задач | `k logs deploy/aspm-aspm-worker -c worker`, ping из smoke. Ожидаются Ready/PONG и доступ к очереди | Проверьте broker, queue, Beat и актуальный release image. SRE эскалирует при росте backlog |
| ScanRun завис в PROCESSING | GET ScanRun, attempt/started_at, worker active и outbox. Проверьте hard time limit | Дождитесь автоматического восстановления по fencing, проверьте отсутствие дублей. SRE исследует активную задачу и storage |
| ScanRun FAILED | GET ScanRun error_code, scanner type и SHA. Сопоставьте worker logs | После исправления временной причины выполните scoped retry. Для неверного файла отправьте исправленный payload с новым ключом |
| Outbox backlog | System Health, Beat logs, broker PING, oldest pending. Один активный Beat | Восстановите DB/broker/Beat, проконтролируйте drain и статусы. DBA/SRE при fencing или длительных блокировках |
| Webhook delivery failure | Delivery history, HTTP status, attempts, TLS и DNS approved destination | Владелец устраняет TLS/5xx или HMAC mismatch. Replay по согласованию, дедуп Delivery ID, запись аудита |
| PostgreSQL CPU saturation | `pg_stat_activity`, locks, CPU, I/O, WAL. Сопоставьте с импортами/отчётами | DBA диагностирует нагрузку и меняет throttling/расписание. Смотрите latency и очередь после стабилизации |
| Exhausted DB connections | `SHOW max_connections;` и число по ролям. Учитывайте rollout | Остановите параллельные rollout, уменьшите конкурентность по согласованию, проверьте доступные слоты. Эскалация DBA |
| Storage unavailable | `k describe pvc CLAIM`, read/rename/fsync probe. Ожидаются Bound и доступ двух реплик | SRE/CSI восстанавливает mount; проверьте целостность fixtures и report download |
| PVC Pending | `k describe pvc CLAIM`, events, SC binding mode и quota | Исправьте provisioning/zone классов, дождитесь Bound. Новый PVC не должен подменять существующие данные |
| Artifact checksum mismatch | Сопоставьте DB checksum, байты из доверенного backup и результаты разных реплик | Изолируйте повреждение, зафиксируйте audit, восстановите согласованную копию. Эскалация SRE/owner |
| Ingress 502/503 | `k get endpointslice`, ingress и pod events, HTTP readiness | Исправьте backend, ingress class/cert или policy, проверьте опубликованный URL без retries |
| OOMKilled | `k describe pod POD`, reason и memory request/limit | SRE перепроверяет concurrency/batch и лимиты, исключает повтор под согласованной нагрузкой |
| DiskPressure | `kubectl --context "$ASPM_CONTEXT" describe node NODE`, capacity/inode alarms | SRE увеличивает capacity или освобождает подтверждённые временные данные. PVC и защищённые данные остаются под контролем владельца |
| Failed upgrade | Helm history, hook Job, endpoint readiness, Application SHA | Заморозьте параллельный rollout, проверьте schema-review. Исправьте причину и повторите smoke |
| Rollback | Успешная revision, DB schema review и backup | [Процедура](15_UPGRADE_ROLLBACK.md). Выполните smoke и проверку оригиналов после переключения |
| Restore after failure | RPO/RTO, checksum dump и согласованные DB/PVC snapshots | [Восстановление](14_BACKUP_RESTORE.md) в пустую цель, сверка объектов, RBAC и только потом переключение ingress по решению владельца |

Пороги и контакты заполните после настройки мониторинга. DBA __________ · SRE __________ · IAM __________ · ASPM owner __________
