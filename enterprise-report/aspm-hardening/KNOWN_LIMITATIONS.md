# Known limitations and blocking gates

1. No Kubernetes cluster/context: actual install/upgrade/rollback/scaling, policy enforcement and pod lifecycle are NOT TESTED. Provision the reviewed lab and run the smoke/failure campaign.
2. No production storage: RWX ownership, fsync/rename semantics, concurrent multi-node access, quota/retention and database+evidence restore are NOT QUALIFIED. An S3 backend was not added; the chart uses the explicitly allowed shared-filesystem alternative.
3. Full 1M Core9/Acceptance and Ryzen/Linux AMD64 builds are NOT TESTED. Free Mac disk is below the guarded campaign budget. Do not disable guards or compare ARM64 timings as native AMD64 A/B.
4. Webhook transport/state/RBAC tests and browser flows are covered, but real consumer stress, real worker process death around HTTP ACK and cluster broker/storage outages need further qualification. Internal/private endpoints are intentionally unsupported. History retention requires an operator-reviewed policy; pending queues have explicit caps/dead letters.
5. Telemetry is partial: durable queue gauges are implemented; global worker latency/queue-wait/RSS and PostgreSQL CPU/WAL/I/O require external exporters. Correlation spans ScanRun/events, not full distributed tracing. OIDC/AD SSO is a future independently tested milestone.

No stable publication, registry push, production promotion or protected data deletion was performed. PRODUCTION READY and READY FOR 5M are not assigned.
