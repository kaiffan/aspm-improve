# Анкета инфраструктуры | Standard HA

Заполняйте имена, идентификаторы и Secret references. Пароли, токены, database URI с credentials и private key хранятся в корпоративном Vault.

| Блок / параметр | Требуется | Default / пример и формат | Helm path / где используется | Владелец | Значение |
|---|---|---|---|---|---|
| Kubernetes context | Да | staging-eu, kubeconfig name | `--context` | Kubernetes | ____ |
| Namespace / release | Да | aspm-stage / aspm, DNS labels | `--namespace`, `--release` | Kubernetes | ____ |
| Linux arch | Да | amd64 или arm64 | `nodeSelector.kubernetes.io/arch`, `--arch` | Kubernetes | ____ |
| Registry Django / nginx | Да | registry.example.invalid/aspm/django, nginx | `image.repository`, `nginxImage.repository` | ASPM owner | ____ |
| Immutable digests | Да | sha256 + 64 hex из registry | `image.digest`, `nginxImage.digest` | ASPM owner | ____ |
| Pull Secret | Для private registry | name deploy-pull и ключ .dockerconfigjson | `imagePullSecrets[].name` | Kubernetes | ____ |
| Application SHA | Да | 40 hex из manifest | `config.DD_ASPM_GIT_SHA` | ASPM owner | ____ |
| CPU/RAM и reserve | Да | проектные 16 vCPU / 32 GiB app | `web.resources`, `worker.resources`, `beat.resources`, `migrations.resources` | Kubernetes | ____ |
| Ingress class / namespace / selector | Да | traefik / ingress-system / matchLabels | `ingress.className`, `networkPolicy.ingressNamespace`, `networkPolicy.ingressPodSelector` | Kubernetes | ____ |
| Host / public URL | Да | FQDN и https URL | `ingress.host`, `config.DD_ALLOWED_HOSTS`, `config.DD_SITE_URL` | Kubernetes | ____ |
| Ingress TLS Secret | Да | aspm-tls, tls.crt и tls.key | `ingress.tlsSecretName` | Kubernetes | ____ |
| PostgreSQL host/port | Да | private FQDN:5432, TLS name | `existingSecret` → `secretKeys.databaseUrl` | DBA | ____ |
| PostgreSQL DB / role | Да | aspm_stage / aspm_app, отдельные | runtime Secret, URI | DBA | ____ |
| PostgreSQL version | Да | лаборатория 18.6 | внешний сервис | DBA | ____ |
| DB schema privileges | Да | DDL/extension согласно migration plan | runtime DB role | DBA | ____ |
| Runtime Secret / DB URI key | Да | aspm-runtime / database-url | `existingSecret`, `secretKeys.databaseUrl` | Kubernetes/DBA | ____ |
| App session / credential encryption key names | Да | django-secret-key / credential-aes-key | `secretKeys.secretKey`, `secretKeys.credentialKey` | Kubernetes | ____ |
| DB TLS / mode / CA | Да | verify-full / aspm-postgres-ca / ca.crt | `config.DD_DATABASE_OPTIONS`, `databaseTLS.existingSecret` | DBA | ____ |
| DB private CIDR | Да | /32, уточнить failover endpoints | `networkPolicy.egress` | DBA/Kubernetes | ____ |
| Pooler / connections | Да | прямой или session pooling / 100 | вне Helm, `config.DD_DATABASE_CONN_MAX_AGE` 60 | DBA | ____ |
| DB capacity/backup | Да | GiB, WAL retention, RPO/RTO | вне Helm | DBA | ____ |
| Keycloak issuer / realm | Да | https://sso.example.invalid/realms/aspm | `oidc.enabled`, `oidc.issuer` | IAM | ____ |
| Keycloak client ID / Secret/key | Да | aspm / aspm-oidc-client / oidc-client-secret | `oidc.clientId`, `oidc.existingSecret`, `oidc.clientSecretKey` | IAM/Kubernetes | ____ |
| OIDC callback / logout | Да | https://HOST/sso/callback, logout redirect https://HOST/login | `oidc.callbackUrl`, `oidc.providerLogout` | IAM | ____ |
| OIDC CA / client auth | При частном CA / да | CA Secret ca.crt / client_secret_basic | `oidc.existingCaSecret`, `oidc.clientAuth` | IAM | ____ |
| Role и group claims | Да | aspm_roles и aspm_product_grants | `oidc.roleClaim`, `oidc.groupClaim` | IAM | ____ |
| SecOps / Expert / User | Да | aspm-secops / aspm-expert / aspm-user | `oidc.secopsRole`, `oidc.expertRole`, `oidc.userRole` | IAM / ASPM owner | ____ |
| Проектные группы User | Да | доверенный claim → Project ID | Access Management, вне Helm | IAM / ASPM owner | ____ |
| SSO session и group TTL | Да | 3600 / 300 секунд | `oidc.sessionAge`, `oidc.groupTtl` | IAM | ____ |
| Broker endpoint/port/TLS | Да | rediss URI, согласованный порт, отдельный HA сервис | `secretKeys.brokerUrl`, `networkPolicy.egress` | Kubernetes | ____ |
| Cache endpoint/port/TLS | Да | отдельный rediss URI, согласованный порт и HA | `secretKeys.cacheUrl`, `networkPolicy.egress` | Kubernetes | ____ |
| StorageClass / режим доступа | Да | CSI с RWX и snapshot | PVC вне Helm | Kubernetes | ____ |
| Evidence/media claim names | Да | aspm-evidence / aspm-media | `storage.existingClaim`, `storage.mediaExistingClaim` | Kubernetes | ____ |
| Capacity и mount | Да | GiB, fsync/rename, UID 1001/GID 1337 | `storage.minimumFreeBytes`, `podSecurityContext` | Kubernetes | ____ |
| Backup и retention PVC | Да | snapshot policy, GiB, дни | вне Helm | DBA/Kubernetes/owner | ____ |
| DNS, ingress и egress | Да | TCP/UDP 53, 443/8080, все endpoints | `networkPolicy.enabled`, `networkPolicy.egress` | Kubernetes | ____ |
| Webhook destinations | Если включены | разрешённые HTTPS DNS/IP | `networkPolicy.egress`, `config.DD_ASPM_WEBHOOKS_ENABLED` | ASPM owner | ____ |
| ServiceMonitor / selectors | Если доступно | disabled, selectors Prometheus | `monitoring.serviceMonitor` | Kubernetes | ____ |
| Контакты и окно | Да | DBA, SRE, IAM, ASPM owner / дежурные каналы | вне Helm | ASPM owner | ____ |
