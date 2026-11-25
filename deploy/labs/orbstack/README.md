# Local ASPM on OrbStack Kubernetes

This lab uses only the `orbstack` context and a namespace with the `aspm-lab-` prefix. PostgreSQL, broker, cache and all PVCs belong to that namespace. `local-path` is single-node storage. The profile exposes a ClusterIP Service, uses local images, and enables webhook management and the opt-in HTTP test hook.

Required image tags are listed in `values.yaml` and `dependencies.yaml`. OrbStack shares its image store with Kubernetes. Build the ASPM ARM64 images from the cached bases as described in [the release bundle](../../../enterprise-report/aspm-hardening/release-bundle/README.md). Use the exact matching PostgreSQL/Valkey development images described by the manifests.

```sh
deploy/labs/orbstack/install.sh
# Only for an existing namespace created by this installer
deploy/labs/orbstack/install.sh --resume
```

The resume flow retains existing credentials and PVCs. A timed-out volume-owner Job is replaced only after the node reports `DiskPressure=False`. The owner Job grants the app uid 1001 ownership of the lab evidence and media claims so web/worker can run nonroot. `helm test` checks the real login endpoint. The test hook is included in chart `0.1.0-rc.2`.

Once `helm test` passes, run the HTTP/worker webhook smoke from an ASPM pod:

```sh
deploy/labs/orbstack/run-webhooks.sh > webhook-smoke.json
```

It creates a new synthetic project, admin, project viewer, repository-scoped service token and two subscriptions. Test endpoint hostnames use the reserved `.invalid` suffix. The script compares delivery history before and after a real scan, replay and secret rotation. It checks viewer denial and private endpoint validation. The fixture scripts are intended for this disposable database. Positive TLS and HMAC verification are covered by `unittests.test_aspm_webhook_tls` using a local test receiver and test-only resolver mapping.

For a local browser on a running release, forward the Service to `127.0.0.1:18735`:

```sh
kubectl --context orbstack -n aspm-lab-orbstack port-forward \
  --address 127.0.0.1 service/aspm-aspm 18735:80
```
