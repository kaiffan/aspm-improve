# Data integrity

The development runs use disposable PostgreSQL databases and private volumes with the integration lab's project name. Runtime evidence and test fixtures use separate databases and cache namespaces. No protected Mac database or existing Docker volume was used for destructive operations.

Existing artifact checksums, immutable observations, completed Run protection and report manifests remain in force. PostgreSQL checks ScanRun Product, Commit, pinned Engagement and Test relationships. A new policy scope or IdP state does not rewrite history.

The frozen native performance workload includes its original input checksums and restore fingerprints. Protected million-row dataset checks were not repeated as part of this local lab.

The local restore compared eight tables and verified 27 artifact/report SHA-256 values. Both sides contained 21 ScanRuns, 87 Findings, 87 historical observations, three generated reports, one policy, one managed binding, six SSO identities and two Product grants. This scope uses a PostgreSQL dump and evidence tar from the isolated lab. [Restore manifest](raw/local-restore.json)
