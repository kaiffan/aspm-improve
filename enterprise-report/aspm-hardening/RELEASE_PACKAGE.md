# Release package

The local [release bundle](release-bundle) contains the versioned Helm package `aspm-0.1.0-rc.1.tgz`, example values, local ARM64 smoke Dockerfiles, source and image provenance, and `SHA256SUMS`. Verify file checksums with `sha256sum -c SHA256SUMS` from that directory. Container image IDs identify local images. A registry manifest digest remains unset until images are built, published and verified in the target registry.

The two smoke images layer the application source and changed static assets on existing Linux ARM64 images. The native build uses the repository's full Dockerfiles on a Linux AMD64 host. The build wrapper and performance campaign preserve the frozen fixtures and protected snapshot guards. See [REPRODUCE.md](REPRODUCE.md) and [the native kit](../../integration-report/zero-finalize-final-qualification/native).

| Topic | Artifact |
|---|---|
| Deployment values and Secret keys | [HELM_VALUES.md](HELM_VALUES.md) |
| Migration, upgrade and rollback | [MIGRATION_AND_ROLLBACK.md](MIGRATION_AND_ROLLBACK.md) |
| Storage backup and recovery | [STORAGE_ARCHITECTURE.md](STORAGE_ARCHITECTURE.md), [OPERATIONS_RUNBOOKS.md](OPERATIONS_RUNBOOKS.md) |
| Monitoring and alerts | [OBSERVABILITY.md](OBSERVABILITY.md) |
| Ingestion API and CI/CD | [API_AND_CI.md](API_AND_CI.md) |
| Webhook payload and verification | [WEBHOOK_EVENTS.md](WEBHOOK_EVENTS.md), [WEBHOOK_SECURITY.md](WEBHOOK_SECURITY.md) |
| Release qualification | [RELEASE_GATE.md](RELEASE_GATE.md), [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) |
