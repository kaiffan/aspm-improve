# Release gates

Application source `5133e155d102eb0f431560924ea129b2287319ff`. Chart `0.1.0-rc.1` at `f37a65b62248bdd9efe53e74137b13e79796cb8f`. See [SHA-256 and commit provenance](provenance.json).

| Gate | Status | Evidence |
|---|---|---|
| CODE COMPLETE | PARTIAL | Helm, webhook workflow, storage integrity and UX are implemented and exercised. Full telemetry and end-to-end correlation still have gaps. |
| HELM VALIDATED | PASS | 11 chart tests, typed values schema, 48 Kubernetes resources across five renders, local read-only image smoke. |
| KUBERNETES DEPLOYED | NOT TESTED | No cluster or current context was available. |
| STORAGE QUALIFIED | LOCAL PASS, TARGET NOT TESTED | Worker-to-web shared volume and verified downloads. Local DB and archive restore matched 206 immutable file references. Kubernetes RWX/CSI multi-node checks remain. |
| WEBHOOK QUALIFIED | LOCAL PASS | Transactional event capture, pinned verified TLS/HMAC, independent writes, retries, replay, worker-loss recovery state, revocation and RBAC tests. External sustained delivery and Kubernetes failure qualification remain. |
| UX VALIDATED | LOCAL PASS | Playwright on Linux ARM64 images, 66 page/viewport/theme runs and the management workflow. |
| LOCAL REGRESSION PASS | PASS | Django 8,335 passed, 553 skipped, 0 failures, 0 errors. JavaScript 17/17. |
| PERFORMANCE REVIEW PASS | NOT TESTED | Core9 and Acceptance 1M paired runs still require the native host and disk. |
| AMD64 BUILD PASS | NOT TESTED | Both local smoke image builds are Linux ARM64. Native build plan resolves A and B. |
| RYZEN 1M QUALIFIED | NOT TESTED | No native Ryzen qualification node was available. |
| READY FOR 5M | NOT ASSESSED | 1M, target monitoring and target restore gates are open. |
| PRODUCTION READY | NOT QUALIFIED | Target platform, operational and performance gates remain. |

## Measured on the local ARM64 lab

- 100 API-only scans from 10 concurrent clients and 10 repository-scoped tokens, with one finding each. Completion took 12.39 s end-to-end, or 8.07 scans/s. Admission p50/p95/p99 were 195/589/628 ms. This synthetic smoke shares a host with other jobs. [Raw ingestion measurements](raw/ingestion-smoke.json)
- Worker memory was 361.7 MiB in one Docker sample just after load. Peak memory, PostgreSQL CPU, WAL and I/O attribution, and webhook latency under sustained load were NOT TESTED. [Resource sample](raw/image-resource-sample.jsonl)
- The broker outage left liveness at 200 and readiness at 503. A scan accepted during the outage completed after restart, and the evidence downloads matched. A separate smoke accepted a scan while the worker was stopped and completed it after two workers started. [Broker recovery](raw/broker-recovery.json) · [Worker recovery](raw/worker-recovery.json)
- The preflight validated the migrated schema and writable evidence storage. A second migrator failed while the PostgreSQL lock was held and succeeded after release. [Preflight](raw/image-preflight.txt) · [Migration fence](raw/migration-fencing.txt)
- The full Django run used a fresh database and took 826.1 s. [Summary](raw/full-django-summary.json) · [Raw log](raw/full-django-committed-fixtures.log.gz)

## Next qualification targets

1. Set up a Kubernetes lab with the intended ingress, PostgreSQL and shared CSI. Run actual install/upgrade, replacement of web and worker pods across nodes, broker and PostgreSQL failure/recovery, migration compatibility and restore checks. The smoke entrypoint is `deploy/scripts/kubernetes-smoke.sh`.
2. Build on native Linux AMD64 and run the frozen 1M Core9/Acceptance A/B campaign. The Mac had 6.3 GiB free and the native campaign requests 51 GiB including reserve. [Capacity preflight](raw/capacity.json) · [Native reproduction](REPRODUCE.md)
3. Qualify the webhook service with a target TLS receiver, measured delivery latency and recovery under sustained traffic. Finish cross-worker telemetry and report correlation, then review rollout readiness and staged restore evidence.
