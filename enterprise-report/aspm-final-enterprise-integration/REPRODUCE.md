# Reproduce the integration evidence

Use the exact application checkpoint in [source provenance](raw/source-provenance.json). Prepare an isolated Docker Compose lab with separate PostgreSQL test and runtime databases, separate cache and broker namespaces, and disposable evidence storage. Preserve any existing user volumes. See the [Keycloak lab](../../deploy/labs/keycloak/README.md) for local HTTPS setup, synthetic users, provisioning and browser commands.

## Application and chart

```sh
export COMPOSE_PROJECT_NAME=aspm-final-enterprise-integration
export COMPOSE_FILE=path/to/isolated-compose.json
./run-unittest.sh --test-case unittests
docker compose exec -T uwsgi python manage.py makemigrations --check --dry-run
docker compose exec -T uwsgi python manage.py spectacular --fail-on-warn
node --test release/1.0.1/scripts/*.test.cjs
deploy/scripts/validate-chart.sh .cache/helm-evidence
```

After the TLS lab is ready, download its dedicated schema with `curl --fail --cacert .cache/keycloak/localhost.crt https://localhost:48141/api/aspm/v1/openapi/`. The general spectacular command checks the v2 schema.

The chart validator requires Helm, kubeconform, PyYAML and jsonschema. Render with the optional OIDC values and a test Secret reference, then use server-side Kubernetes dry run against an owned context. Keep the configured test and live cache indexes distinct even when the Redis server is local.

## Local query and restore checks

Execute [measure_local_queries.py](measure_local_queries.py) in the seeded lab Django shell. It rolls back temporary ScanRuns and entitlement mappings. The [SSO workload](sso_workload.cjs) runs local parallel logins or checks expiry after stopping the isolated IdP. Pass the isolated runtime and restore databases through the [hash-only restore manifest](../../deploy/labs/keycloak/restore_manifest.py). Export the runtime with PostgreSQL custom-format dump, restore with `pg_restore --exit-on-error --no-owner --no-acl` to a fresh `aspm_final_restore` database, restore the evidence tar into a new volume and compare the manifests. Keep dumps, tar files, credentials and raw service logs private.

## Native strict A/B

The [incremental source bundle](raw/aspm-final-integration.bundle) can be verified with git bundle verify in a checkout that contains the hardening baseline. On native Linux/AMD64, provision enough workspace capacity, install the toolchain documented in the original native kit and use a new state directory. The native wrapper accepts the later enterprise-hardening baseline while preserving the original workloads and database safety checks.

```sh
aspm_a=0011c221aba7d968ae0734dc1897a087fd9d55e6
aspm_b=7328daa441129bad49abd956e273e624362e655e
aspm_state="$PWD/.cache/aspm-final-native"
python3 deploy/scripts/native.py --baseline "$aspm_a" --candidate "$aspm_b" build --repo "$PWD" --state "$aspm_state"
for phase in init seed core9 acceptance; do
  python3 deploy/scripts/native.py --baseline "$aspm_a" --candidate "$aspm_b" campaign --state "$aspm_state" "$phase"
done
python3 deploy/scripts/native.py --baseline "$aspm_a" --candidate "$aspm_b" summarize --state "$aspm_state"
```

Before deployment, run the existing Kubernetes smoke and restore procedure in the target environment. Verify egress to the approved Keycloak endpoint, CSI behavior under the runtime UID, PostgreSQL migrations, worker operations and webhook delivery. [Existing native kit](../../integration-report/zero-finalize-final-qualification/native) · [Staging and native prerequisites](../aspm-hardening/REPRODUCE.md)
