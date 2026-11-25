# Operations runbooks

| Symptom | First evidence | Recovery / verification |
|---|---|---|
| PostgreSQL unavailable | readiness 503, primary connection/HA events, exporter connections/locks | Restore the primary/TLS path; do not restart healthy web solely on transient DB loss. Verify schema/preflight and outbox recovery. |
| Broker unavailable | readiness 503, dispatcher deferred log, durable backlog/age | Restore broker connection/credentials; pending jobs remain in PostgreSQL. Observe completion and absence of lost scans. |
| Celery stuck / OOM | task IDs, worker RSS/limits, queue age, pod termination reason | Drain with SIGTERM and sufficient grace. Replace unhealthy workers; inspect recovery limit/FAILED state. Never normalize SIGKILL updates. |
| Outbox backlog | pending/unexpanded count and oldest age, dispatcher logs, beat owner | Verify single scheduler, available worker queue, PostgreSQL locks and broker. Recover the existing dispatcher; do not add a competing mechanism. |
| ScanRun FAILED | safe error code, scanner/artifact SHA, attempt/recovery count | Verify private original and parser input on an owned copy; retry through scoped API only. Preserve historical generations. |
| Webhook backlog/dead letters | delivery/attempt history, capacity_limit/http/network codes | Fix endpoint/DNS/TLS/rate/configuration, then explicit replay. Deduplicate receivers by event ID. Do not log consumer bodies or secrets. |
| Storage unavailable/corrupt | safe download 503, quota/free bytes, checksum manifest | Restore shared storage/permissions, verify exact checksums and referenced paths. Do not replace evidence with new scan bytes. |
| Migration failed | retained hook Job logs, migration plan, pg_locks | Remove blockers/repair dependency after backup; rerun controlled migration. Pods must stay fenced. Do not pretend Helm rolls back PostgreSQL schema. |
| High DB CPU / slow overview | query plans/buffers, active statements/waits, route SQL counts | Compare same-data plans and cardinalities. Keep selectors/pagination bounded; fix measured query regressions rather than raising limits. |
| Backup/restore | database snapshot + private evidence inventory/checksums + separately stored encryption key | Restore to an isolated DB/PVC, run preflight, validate checksums/RBAC/history, then review cutover. |
| Upgrade/rollback | immutable image/source digests, schema compatibility, verified backup | Use migration Job and fenced rollout. Roll back compatible workload/configuration explicitly; review schema state separately. |

Alert on oldest pending age, sustained readiness failure, dead letters/capacity limits, evidence free-space reserve, task recovery failures and exporter availability. Thresholds must be calibrated on the target workload and alert route; no production alert receiver is silently configured.
