# ASPM enterprise hardening release bundle

This bundle is a local candidate for evaluation. See [release gates](../RELEASE_GATE.md) and [reproduction](../REPRODUCE.md). Verify `SHA256SUMS` from this directory before installing the chart.

The source bundle contains the implementation and chart commits. Restore it into a checkout that already contains `1ed9e9f396e11314514d58176db43af805e128ec` with `git bundle verify` and `git fetch ./aspm-hardening-source.bundle HEAD:refs/heads/feature/aspm-enterprise-hardening`. Keep both provenance SHAs for the native performance runner. The frozen native kit, `deploy/scripts/native.py`, and full production Dockerfiles are in the repository history.

The ARM64 Dockerfiles describe an incremental local smoke build from cached bases. For the Django build context, extract `git archive <application-sha> dojo`. For the nginx build context, copy the application SHA's `dojo/static/dojo/css/aspm.css` and `dojo/static/dojo/js/aspm.js` as `aspm.css` and `aspm.js`. Set the Docker build argument `REVISION` to the application SHA and use `--platform=linux/arm64`. Local images are identified by the Docker image IDs in `local-images.json`.

The Kubernetes chart requires existing Secrets, PVCs, and dependency network rules. Use a verified private image registry and the `values-staging.yaml` or `values-production.example.yaml` override. `prometheus-rules.example.yaml` is a raw Prometheus rule file. Scope rules to the intended cluster and release before enabling them and choose thresholds appropriate for traffic.

The API spec is `openapi.yaml`. See [API and CI/CD examples](../API_AND_CI.md), [webhook contract](../WEBHOOK_EVENTS.md), and [migration and recovery](../MIGRATION_AND_ROLLBACK.md).
