# Helm chart

`deploy/helm/aspm`, chart `0.1.0-rc.1`, appVersion `1.0.1-enterprise-rc`. Separate web, worker and beat Deployments. Web has Django and nginx containers with matching source images. HTTP service exposes only nginx; dependency probes and metrics use the application port. Beat has one replica, Recreate rollout and a database session lock. Workers use prefork, configurable queues/concurrency, prefetch=1 and 960-second termination grace, exceeding the existing ingestion 900-second hard limit.

Migration hooks use only pre-existing Secrets, so first-install hooks do not depend on release ConfigMaps or ServiceAccounts. A PostgreSQL lock serializes migration executors; backoffLimit=0 leaves failed hooks for diagnosis. Each application pod runs aspm_preflight against the complete migration graph and evidence storage. Disabling the migration Job requires an operator-managed migration before pods become ready.

Optional ingress requires TLS. HPA, PDB, ServiceMonitor and Helm HTTP test hook are configurable. Root values control scheduling, resources, pod metadata and security. Default egress permits DNS only: supply actual database, broker, cache and approved destination rules before deployment. Helm never creates passwords, PostgreSQL or evidence volumes.

See raw/helm-qualification.txt and generated chart README. No actual Kubernetes deployment was performed.
