# ASPM enterprise hardening qualification

This local candidate adds an ASPM Helm chart, durable outbound webhook delivery and management, evidence integrity checks, and operational probes. Browser workflows and manifest validation run against the candidate. The local images are Linux ARM64 and use the rendered chart commands for the web, worker and beat smoke. See [RELEASE_GATE.md](RELEASE_GATE.md) for measured results and [provenance.json](provenance.json) for code and artifact IDs.

Production qualification requires a real Kubernetes deployment, target shared storage and tested restores, native AMD64 build, and the full 1M Core9 and Acceptance campaign. The local bundle is unpublished.
