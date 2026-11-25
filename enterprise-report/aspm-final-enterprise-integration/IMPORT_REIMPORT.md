# Accept, import and retry

CI calls POST /api/aspm/v1/scans/ once per logical delivery. HTTP 202 means the artifact and pending ScanRun are durable. A replay with the same fingerprint and service account returns HTTP 200 and the previous ID. A changed request under the same key returns HTTP 409.

The worker verifies artifact size and SHA-256, reuses the ScanRun's own Test after interruption, and executes the DefectDojo importer and RC5 single-Finding write protocol. It snapshots Findings before completing the scan and publishes the observation generation in the same update as the completed state. Worker replay after completion does not parse again.

A new delivery uses a new Test, even when its Engagement is shared. Findings from absent or unsuccessful scans do not establish mitigation. The environment forms part of the evidence slot alongside scanner and declared scan scope. Historical reports keep the original selection and generation.

An accepted processing failure is recorded on its Run. A failure before durable acceptance can be retried using the same delivery key. The periodic dispatcher recovers database-committed work when the immediate Celery wake fails. The original artifact is available for authorized diagnostics. Analysts can create later immutable exports through the commit's report page.
