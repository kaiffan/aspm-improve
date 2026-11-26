# ASPM Helm chart

Unpublished release candidate. External PostgreSQL, separate Redis/Valkey broker/cache URLs,
private RWX evidence and shared media claims are required. No database or credential is generated.

Provision `aspm-runtime` with `django-secret-key`, `credential-aes-key`, `database-url`, `broker-url`,
`cache-url`; provision the PostgreSQL CA Secret and the two RWX PVCs before installation.
The database URL must identify the primary. Advisory locks require a direct or session-pooled connection.
Configure dependency CIDRs/selectors in `networkPolicy.egress`; the default permits only DNS.
For Keycloak, set `oidc.enabled`, issuer, exact HTTPS callback URL, client ID and existing Secret reference.
Set `oidc.existingCaSecret` if the IdP uses a private CA. Allow HTTPS egress to the issuer and ensure the ingress
overwrites `X-Forwarded-Proto`. Keep callback query strings out of ingress access logs.
Use verified immutable Django/nginx images from the same application source, pinned by digest in production.

```sh
helm lint deploy/helm/aspm
helm template aspm deploy/helm/aspm -f deploy/helm/aspm/values-staging.yaml
helm upgrade --install aspm deploy/helm/aspm -n aspm-staging --create-namespace \
  -f /secure/aspm-staging.yaml --wait --timeout 35m
helm test aspm -n aspm-staging --logs
```

Set `tests.enabled=true` to install the optional Helm ClusterIP HTTP test hook. The latest test Pod is
retained until the next run for diagnosis. See [external PostgreSQL setup](../../../deployment/EXTERNAL_POSTGRESQL_INPUT_REQUIRED.md). Migrations use a pre-install/upgrade
Job with a PostgreSQL lock. Web/worker/beat init containers block on the entire migration graph and
private-storage preflight. Jobs use only pre-existing Secrets and have no dependency on release ConfigMaps
or ServiceAccounts. Failed hooks remain for diagnosis. Beat has one replica, Recreate updates and database
session fencing. Ingestion and webhook outbox recovery share the existing periodic dispatcher; no second
scheduler is deployed. Worker SIGTERM grace is longer than the ingestion task limit.

Read [operations and gates](../../../enterprise-report/aspm-hardening/REPRODUCE.md), especially storage,
upgrade, backup/restore and NetworkPolicy limitations. Never infer Kubernetes readiness from rendering.
Read-only containers use explicit writable `/tmp`, runtime, evidence and media mounts. Root-squashed RWX
ownership must be provisioned for UID 1001/GID 1337. Non-root compatibility still needs CSI qualification.

This table is generated from values.yaml by tests/generate_readme.py.

| Key | Type | Default |
|---|---|---|
| `nameOverride` | `str` | `` |
| `fullnameOverride` | `str` | `` |
| `image.repository` | `str` | `aspm/django` |
| `image.tag` | `str` | `1.0.1-enterprise-rc` |
| `image.digest` | `str` | `` |
| `image.pullPolicy` | `str` | `IfNotPresent` |
| `nginxImage.repository` | `str` | `aspm/nginx` |
| `nginxImage.tag` | `str` | `1.0.1-enterprise-rc` |
| `nginxImage.digest` | `str` | `` |
| `nginxImage.pullPolicy` | `str` | `IfNotPresent` |
| `imagePullSecrets` | `list` | `[]` |
| `existingSecret` | `str` | `aspm-runtime` |
| `secretKeys.secretKey` | `str` | `django-secret-key` |
| `secretKeys.credentialKey` | `str` | `credential-aes-key` |
| `secretKeys.databaseUrl` | `str` | `database-url` |
| `secretKeys.brokerUrl` | `str` | `broker-url` |
| `secretKeys.cacheUrl` | `str` | `cache-url` |
| `config.DD_ALLOWED_HOSTS` | `str` | `localhost,aspm.example.invalid` |
| `config.DD_SITE_URL` | `str` | `https://aspm.example.invalid` |
| `config.DD_DEBUG` | `str` | `False` |
| `config.DD_TRACK_MIGRATIONS` | `str` | `True` |
| `config.DD_ASPM_INGESTION_ENABLED` | `str` | `True` |
| `config.DD_ASPM_DEFAULT_ENGAGEMENT_POLICY` | `str` | `default` |
| `config.DD_ASPM_API_ONLY` | `str` | `True` |
| `config.DD_ASPM_SCM_HIERARCHY` | `str` | `True` |
| `config.DD_ASPM_WEBHOOKS_ENABLED` | `str` | `False` |
| `config.DD_ASPM_ARTIFACT_ROOT` | `str` | `/app/aspm-private` |
| `config.DD_DJANGO_METRICS_ENABLED` | `str` | `True` |
| `config.DD_DATABASE_CONN_MAX_AGE` | `str` | `60` |
| `config.DD_DATABASE_OPTIONS` | `str` | `{"connect_timeout":3,"sslmode":"verify-full","sslrootcert":"/app/db-tls/ca.crt"}` |
| `config.DD_SESSION_COOKIE_SECURE` | `str` | `True` |
| `config.DD_CSRF_COOKIE_SECURE` | `str` | `True` |
| `config.DD_SECURE_PROXY_SSL_HEADER` | `str` | `True` |
| `oidc.enabled` | `bool` | `False` |
| `oidc.issuer` | `str` | `` |
| `oidc.callbackUrl` | `str` | `` |
| `oidc.clientId` | `str` | `` |
| `oidc.existingSecret` | `str` | `` |
| `oidc.clientSecretKey` | `str` | `oidc-client-secret` |
| `oidc.clientAuth` | `str` | `client_secret_basic` |
| `oidc.scopes` | `str` | `openid` |
| `oidc.roleClaim` | `str` | `aspm_roles` |
| `oidc.groupClaim` | `str` | `aspm_product_grants` |
| `oidc.secopsRole` | `str` | `aspm-secops` |
| `oidc.expertRole` | `str` | `aspm-expert` |
| `oidc.userRole` | `str` | `aspm-user` |
| `oidc.sessionAge` | `int` | `3600` |
| `oidc.groupTtl` | `int` | `300` |
| `oidc.providerLogout` | `bool` | `True` |
| `oidc.existingCaSecret` | `str` | `` |
| `databaseTLS.existingSecret` | `str` | `aspm-postgres-ca` |
| `storage.existingClaim` | `str` | `aspm-evidence` |
| `storage.mediaExistingClaim` | `str` | `aspm-media` |
| `storage.minimumFreeBytes` | `int` | `1073741824` |
| `serviceAccount.create` | `bool` | `True` |
| `serviceAccount.name` | `str` | `` |
| `serviceAccount.annotations` | `dict` | `{}` |
| `podLabels` | `dict` | `{}` |
| `podAnnotations` | `dict` | `{}` |
| `nodeSelector` | `dict` | `{}` |
| `tolerations` | `list` | `[]` |
| `affinity` | `dict` | `{}` |
| `topologySpreadConstraints` | `list` | `[]` |
| `scheduling.enabled` | `bool` | `False` |
| `scheduling.nodePolicy` | `str` | `ScheduleAnyway` |
| `scheduling.preferDistinctNodes` | `bool` | `False` |
| `scheduling.zonePolicy` | `str` | `` |
| `podSecurityContext.runAsNonRoot` | `bool` | `True` |
| `podSecurityContext.runAsUser` | `int` | `1001` |
| `podSecurityContext.runAsGroup` | `int` | `1337` |
| `podSecurityContext.fsGroup` | `int` | `1337` |
| `podSecurityContext.fsGroupChangePolicy` | `str` | `OnRootMismatch` |
| `podSecurityContext.seccompProfile.type` | `str` | `RuntimeDefault` |
| `securityContext.allowPrivilegeEscalation` | `bool` | `False` |
| `securityContext.readOnlyRootFilesystem` | `bool` | `True` |
| `securityContext.capabilities.drop` | `list` | `['ALL']` |
| `web.enabled` | `bool` | `True` |
| `web.replicas` | `int` | `2` |
| `web.processes` | `int` | `2` |
| `web.threads` | `int` | `2` |
| `web.terminationGracePeriodSeconds` | `int` | `150` |
| `web.gracefulDrain` | `bool` | `False` |
| `web.resources.requests.cpu` | `str` | `250m` |
| `web.resources.requests.memory` | `str` | `512Mi` |
| `web.resources.limits.cpu` | `str` | `2` |
| `web.resources.limits.memory` | `str` | `2Gi` |
| `web.nginxResources.requests.cpu` | `str` | `50m` |
| `web.nginxResources.requests.memory` | `str` | `64Mi` |
| `web.nginxResources.limits.cpu` | `str` | `500m` |
| `web.nginxResources.limits.memory` | `str` | `256Mi` |
| `web.startupProbe.httpGet.path` | `str` | `/health/startup` |
| `web.startupProbe.httpGet.port` | `str` | `health` |
| `web.startupProbe.httpGet.httpHeaders` | `list` | `[{'name': 'Host', 'value': 'localhost'}]` |
| `web.startupProbe.failureThreshold` | `int` | `60` |
| `web.startupProbe.periodSeconds` | `int` | `5` |
| `web.startupProbe.timeoutSeconds` | `int` | `5` |
| `web.readinessProbe.httpGet.path` | `str` | `/health/ready` |
| `web.readinessProbe.httpGet.port` | `str` | `health` |
| `web.readinessProbe.httpGet.httpHeaders` | `list` | `[{'name': 'Host', 'value': 'localhost'}]` |
| `web.readinessProbe.failureThreshold` | `int` | `3` |
| `web.readinessProbe.periodSeconds` | `int` | `10` |
| `web.readinessProbe.timeoutSeconds` | `int` | `5` |
| `web.livenessProbe.httpGet.path` | `str` | `/health/live` |
| `web.livenessProbe.httpGet.port` | `str` | `health` |
| `web.livenessProbe.httpGet.httpHeaders` | `list` | `[{'name': 'Host', 'value': 'localhost'}]` |
| `web.livenessProbe.failureThreshold` | `int` | `3` |
| `web.livenessProbe.periodSeconds` | `int` | `15` |
| `web.livenessProbe.timeoutSeconds` | `int` | `3` |
| `worker.enabled` | `bool` | `True` |
| `worker.replicas` | `int` | `2` |
| `worker.concurrency` | `int` | `2` |
| `worker.queues` | `str` | `celery` |
| `worker.readinessProbeEnabled` | `bool` | `False` |
| `worker.pdb.enabled` | `bool` | `False` |
| `worker.pdb.minAvailable` | `int` | `2` |
| `worker.hpa.enabled` | `bool` | `False` |
| `worker.hpa.minReplicas` | `int` | `3` |
| `worker.hpa.maxReplicas` | `int` | `4` |
| `worker.hpa.targetCPUUtilizationPercentage` | `int` | `70` |
| `worker.terminationGracePeriodSeconds` | `int` | `960` |
| `worker.resources.requests.cpu` | `str` | `250m` |
| `worker.resources.requests.memory` | `str` | `512Mi` |
| `worker.resources.limits.cpu` | `str` | `2` |
| `worker.resources.limits.memory` | `str` | `2Gi` |
| `beat.enabled` | `bool` | `True` |
| `beat.terminationGracePeriodSeconds` | `int` | `60` |
| `beat.resources.requests.cpu` | `str` | `50m` |
| `beat.resources.requests.memory` | `str` | `128Mi` |
| `beat.resources.limits.cpu` | `str` | `500m` |
| `beat.resources.limits.memory` | `str` | `512Mi` |
| `migrations.enabled` | `bool` | `True` |
| `migrations.activeDeadlineSeconds` | `int` | `1800` |
| `migrations.lockWaitSeconds` | `int` | `120` |
| `migrations.resources.requests.cpu` | `str` | `250m` |
| `migrations.resources.requests.memory` | `str` | `512Mi` |
| `migrations.resources.limits.cpu` | `str` | `2` |
| `migrations.resources.limits.memory` | `str` | `2Gi` |
| `service.port` | `int` | `80` |
| `service.annotations` | `dict` | `{}` |
| `ingress.enabled` | `bool` | `False` |
| `ingress.className` | `str` | `nginx` |
| `ingress.annotations` | `dict` | `{}` |
| `ingress.host` | `str` | `aspm.example.invalid` |
| `ingress.tlsSecretName` | `str` | `aspm-tls` |
| `networkPolicy.enabled` | `bool` | `True` |
| `networkPolicy.ingressNamespace` | `str` | `ingress-nginx` |
| `networkPolicy.ingressPodSelector` | `dict` | `{}` |
| `networkPolicy.egress` | `list` | `[]` |
| `pdb.enabled` | `bool` | `True` |
| `pdb.minAvailable` | `int` | `1` |
| `hpa.enabled` | `bool` | `False` |
| `hpa.minReplicas` | `int` | `2` |
| `hpa.maxReplicas` | `int` | `6` |
| `hpa.targetCPUUtilizationPercentage` | `int` | `70` |
| `monitoring.serviceMonitor.enabled` | `bool` | `False` |
| `monitoring.serviceMonitor.labels` | `dict` | `{}` |
| `monitoring.serviceMonitor.namespaceSelector` | `dict` | `{}` |
| `monitoring.serviceMonitor.podSelector` | `dict` | `{}` |
| `extraEnv` | `list` | `[]` |
| `tests.enabled` | `bool` | `False` |
