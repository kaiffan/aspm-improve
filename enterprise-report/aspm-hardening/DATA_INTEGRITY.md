# Data integrity

Only newly created hardening/baseline test databases and volumes were mutated. Existing release containers, protected 1M seed/snapshot volumes and original untracked files were not deleted or repurposed. Source baseline commits remain unchanged. No historical finding observation or finalized membership migration was edited. DB test fixtures are disposable; browser/runtime fixtures are separate from test DBs and caches.

New events are captured inside business transactions and payload fields are protected by a PostgreSQL trigger. Stable IDs and unique event/subscription deliveries prevent duplicate fanout. Worker recovery may repeat an HTTP request; this is documented at-least-once delivery. Original and generated downloads now check stored checksums before serving. Failed/quota-limited reports publish no paths, and retry/history remain observable.

See raw/storage-red.log.gz for pre-fix corruption reproduction and final regression logs for original/report corruption, absence and quota cases. Cluster/shared-storage/target-backup fingerprints require independent qualification; no prior protected fingerprint is represented as a new measurement.

The final local backup rehearsal restored PostgreSQL into a new disposable database and unpacked the evidence archive into a new private directory. Source and restored manifests matched, and SHA-256 verification passed for 206 referenced files. See [local-restore.json](raw/local-restore.json).
