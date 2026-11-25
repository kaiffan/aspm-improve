# Helm integration

Chart 0.1.0-rc.3 extends the existing rc.1 chart and rc.2 packaging fix. Its OIDC block is disabled by default. Configure issuer, client ID, exact callback, existing Secret and client-secret key. An optional CA Secret supplies issuer trust. Only the web container receives the OIDC secret. Shared runtime settings carry the default Engagement policy and optional branding variables. Scanner support comes from the application parser registry and policy metadata.

Enable HTTPS egress to Keycloak with the existing NetworkPolicy values and restrict ingress reachability to approved components. The ingress must overwrite forwarded protocol and remove auth callback query strings from access logs. The nginx sidecar logs the path without the query string.

The existing pre-upgrade migration Job, private evidence PVC, worker lifecycle and health probes remain the deployment path. Helm lint, render, schema and Kubernetes-manifest validation are recorded independently of Kubernetes install or rollback.
