# Reproduce qualification

Use the exact application SHA and chart commit in [provenance.json](provenance.json). The baseline is `25da29aaff229d3a815e223d8af8bdc4ecca7c5e`.

## Chart

Install Helm, kubeconform 0.6.7, and PyYAML/jsonschema for Python, then run from the repository root.

```sh
python3 -m pip install PyYAML jsonschema
deploy/scripts/validate-chart.sh .cache/aspm-chart-evidence
sha256sum .cache/aspm-chart-evidence/aspm-0.1.0-rc.1.tgz
```

The validator renders four profiles and an extended chart. Set `ASPM_KUBE_SCHEMA_LOCATION` to a local kubeconform schema template if the runner is offline. The optional ServiceMonitor requires an installed Prometheus Operator CRD.

## Django, JavaScript and browser

Use a fresh disposable PostgreSQL test database with the isolated Compose development stack, a separate cache and no production volumes. The repository's wrapper writes its raw log to stdout. Reusing an interrupted `--keepdb` database can retain fixture rows and perturb query counts.

```sh
COMPOSE_PROJECT_NAME=aspm-enterprise-hardening COMPOSE_FILE=/secure/lab-compose.json \
  ./run-unittest.sh --test-case unittests
node --test release/1.0.1/scripts/*.test.cjs
(cd release/1.0.1/browser && npm ci && npx playwright install chromium)
ASPM_TEST_URL=http://127.0.0.1:48135 \
  node enterprise-report/aspm-hardening/browser.cjs /secure/browser-lab-account.json
```

The Playwright account document needs `username`, `password`, `product_id`, `commit_id` and `subscription_id` from a seeded private lab. Give the user platform webhook management permission. Seed at least one completed scan for the commit and a disabled webhook for the subscription. Store credentials with mode 0600. Browser screenshots and reports contain synthetic names only.

## ARM64 smoke

Build smoke layers using the Dockerfiles and metadata in [release-bundle](release-bundle). Point a disposable Compose lab at those images and use the rendered web, nginx, worker and beat commands, explicit writable tmp mounts and shared evidence storage. Run `python manage.py aspm_preflight` before accepting traffic. Set `DD_ASPM_API_ONLY=True` and use separate broker/cache connections. Bind the smoke listener to loopback.

Mount this report directory as `/qualification` on the lab container, then create ten repository-scoped CI tokens in the owned runtime database. Pipe credential JSON directly into a private file. With `lab` set to your Compose project and file (for example as a shell function), run:

```sh
umask 077
lab exec -T -e ASPM_QUALIFICATION_DB=aspm_hardening image-web \
  python manage.py shell --verbosity 0 -c \
  'import runpy; runpy.run_path("/qualification/provision_local_smoke.py", run_name="__main__")' \
  > /secure/ingestion-private.json
lab exec -T image-web python /qualification/local_smoke.py http://127.0.0.1:8080 \
  < /secure/ingestion-private.json
```

To reproduce broker recovery on a separate lab broker, stop that broker only. Confirm `/health/live` is 200 and `/health/ready` is 503 on the internal web listener. Run the smoke with `--mode submit`, save the returned scan record, restart the broker and pass the credential document plus `scan` to `--mode recover`. The smoke verifies durable processing and artifact/report checksums. Ensure the existing beat/worker pair runs throughout the failure and recovery.

## Kubernetes and native AMD64

Populate existing Secret/PVC references and external network policy rules in reviewed values. Run `deploy/scripts/kubernetes-smoke.sh` in the owned lab context and namespace. See [HELM_VALUES.md](HELM_VALUES.md) and [MIGRATION_AND_ROLLBACK.md](MIGRATION_AND_ROLLBACK.md). Run restore and performance qualification in separate owned environments.

On native Linux AMD64 with Docker and enough capacity, run the following. The native runner verifies both source commits, frozen workload inputs and database restoration boundaries. The state directory must not already exist at build time. The build stage needs 45 GiB free. The full campaign preflight includes a 6 GiB reserve above its 45 GiB budget.

```sh
repo="$PWD"
state="$repo/.cache/aspm-native"
mkdir -p "$repo/.cache"
sha=5133e155d102eb0f431560924ea129b2287319ff
(cd release/1.0.1/browser && npm ci && npx playwright install chromium)
export NODE_PATH="$repo/release/1.0.1/browser/node_modules"
python3 deploy/scripts/capacity.py --path "$repo"
python3 deploy/scripts/native.py --candidate "$sha" build --repo "$repo" --state "$state" --plan
python3 deploy/scripts/native.py --candidate "$sha" campaign --state "$state" plan
python3 deploy/scripts/native.py --candidate "$sha" build --repo "$repo" --state "$state"
for phase in init seed core9 acceptance; do
  python3 deploy/scripts/native.py --candidate "$sha" campaign --state "$state" "$phase"
done
python3 deploy/scripts/native.py --candidate "$sha" summarize --state "$state" > "$state/raw/ab-summary.json"
python3 deploy/scripts/native.py --candidate "$sha" campaign --state "$state" load --fixtures "$repo/unittests/scans" --rows 1500
python3 deploy/scripts/native.py --candidate "$sha" campaign --state "$state" stop
```

The campaign writes account files and database artifacts outside `raw`. Review the raw evidence before distributing it. See [the original native kit](../../integration-report/zero-finalize-final-qualification/REPRODUCE.md) for host and Playwright prerequisites.

## Verify a local backup and restore

After the lab has finished its jobs, stop writes or take an equivalent consistent snapshot. Run `storage_manifest.py` in a Django shell against the source lab DB to capture the file references and checksums. Save `pg_dump -Fc --no-owner` and a tar archive of the evidence tree in a private directory. Restore PostgreSQL into a **new** lab database with `pg_restore --exit-on-error --no-owner` and extract the archived files into a **new** directory. Run the manifest script against the restored database too. Set `ASPM_QUALIFICATION_DB` to the exact name of the owned database for each run. The standalone verifier compares the manifests and hashes every restored file:

```sh
python3 enterprise-report/aspm-hardening/verify_restore.py \
  /secure/source-manifest.json /secure/restored-manifest.json /secure/restored-files
```

The lab restored 206 references. Production restore still requires a rehearsal using the target storage and backup configuration. Preserve the Django encryption key and credentials separately from the database and evidence archive.
