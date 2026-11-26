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

## Premium UI and HA lab

The optional HA overlay runs two web pods with paired nginx and Django containers, three worker pods, and one fenced Beat. Keep the current lab Helm values in a private file to retain its Secret names and storage claims. Use the same Git SHA for both images. The build helper overlays Python and the two updated ASPM assets on qualified lab bases.

```sh
export ASPM_LAB_DJANGO_BASE=aspm-dual-lab/django:c5ed33b99c9a
export ASPM_LAB_NGINX_BASE=aspm-dual-lab/nginx:c5ed33b99c9a
bash deploy/labs/orbstack/build-candidate.sh <application-sha>
helm --kube-context orbstack -n aspm-lab-orbstack upgrade aspm deploy/helm/aspm \
  -f /secure/existing-lab-values.yaml -f deploy/labs/orbstack/values-ha.yaml \
  --set-string image.tag=<12-character-sha> --set-string nginxImage.tag=<12-character-sha> \
  --wait --rollback-on-failure --timeout 7m
helm --kube-context orbstack -n aspm-lab-orbstack test aspm --logs --timeout 2m
```

For TLS routing, provision a localhost certificate in the dedicated aspm-lab-ingress namespace. Install pinned official Traefik chart 42.4.1 with the supplied values and --skip-crds. Apply the lab Ingress and its ExternalName Service there. Apply values-ha-ingress.yaml as the final ASPM overlay to select the gateway pods in the ingress NetworkPolicy. Verify the certificate using the lab certificate as a client CA.

```sh
helm --kube-context orbstack -n aspm-lab-ingress upgrade --install aspm-lab-traefik traefik \
  --repo https://traefik.github.io/charts --version 42.4.1 --skip-crds \
  -f deploy/labs/orbstack/traefik-ha-values.yaml --wait --timeout 3m
kubectl --context orbstack -n aspm-lab-ingress apply -f deploy/labs/orbstack/ha-ingress.yaml
kubectl --context orbstack -n aspm-lab-ingress port-forward --address 127.0.0.1 svc/aspm-lab-traefik 18736:443
```

The [qualification report](../../../enterprise-report/aspm-premium-ui-kubernetes-ha/REPRODUCE.md) records tested image digests, rollback, traffic measurements and isolated worker recovery.
