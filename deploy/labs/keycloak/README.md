# Isolated ASPM and Keycloak lab

The lab uses synthetic identities and a private Keycloak realm. Run from the integration checkout. Start with a private Compose file containing the PostgreSQL, Valkey broker, Valkey cache and uwsgi test services described in the [existing isolated test setup](../../../enterprise-report/aspm-hardening/REPRODUCE.md). Use a fresh Compose project and database named `aspm_final_integration`. Bind the checkout under /app. Set test-only database and cache indexes distinct from the runtime service.

```sh
umask 077
python3 deploy/labs/keycloak/prepare.py .cache/keycloak
python3 deploy/labs/keycloak/compose.py /secure/isolated-compose.json .cache/keycloak \
  --nginx-image <local-compiled-nginx-image> --sha "$(git rev-parse HEAD)"
lab() { docker compose -p aspm-final-enterprise-integration -f .cache/keycloak/compose.json "$@"; }
lab up -d postgres broker cache uwsgi
lab exec -T -u 0 uwsgi chown 1001:1337 /app/aspm-private
lab exec -T uwsgi python manage.py complete_initialization
lab up -d keycloak web worker beat tls
lab exec -T web python manage.py shell --verbosity 0 < deploy/labs/keycloak/seed.py > .cache/keycloak/projects.json
```

Use a prebuilt nginx image with compiled static files and the application's normal layout. Wait until the local login route returns HTTP 302. Use the installed Playwright runtime in `release/1.0.1/browser` or set NODE_PATH to its node_modules directory.

```sh
node deploy/labs/keycloak/browser.cjs .cache/keycloak .cache/browser-evidence
node deploy/labs/keycloak/revoke.cjs .cache/keycloak .cache/browser-evidence/revocation.json
```

The tested services bind to loopback, locally trust generated test certificates and use Keycloak's development database. Keep the state directory private. The revocation check removes one synthetic user's group and restores it after verification. Prepare a fresh state directory to regenerate credentials. These services are suitable for local qualification only.
