# Kubernetes security

Containers drop all capabilities, disallow privilege escalation, run as UID 1001/GID 1337, use RuntimeDefault seccomp and a read-only root filesystem. Explicit writable mounts cover /tmp, /var/run/defectdojo, private evidence and media. nginx uses a mounted read-only config, /tmp for buffers and stdout/stderr for logs; its legacy mutating entrypoint is bypassed. ServiceAccount token mounting is disabled; no Kubernetes API RBAC binding is created.

Application probes bypass sessions and settings lookups. /health/live and /health/startup never contact the database/broker. /health/ready uses short PostgreSQL/Redis timeouts and sanitized failures. nginx hides probe and metrics routes from public service traffic. Allow metrics only from explicitly selected monitoring pods/namespaces. Ingress TLS Secret is external. Restrict ingress-controller forwarding headers at the network boundary.

NetworkPolicy requires a CNI that enforces it. Configure actual dependency addresses/selectors. A pre-install migration hook runs before the release's regular policy exists on a brand-new namespace: enforce a namespace baseline policy before installation if required. PodSecurity admission, CNI behavior, certificate lifecycle, root-squashed PVC ownership and node-specific filesystem behavior require real cluster tests. No live Kubernetes security claim is made.
