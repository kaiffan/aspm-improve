# Migration and rollback

Apply migration 0320 for policy and binding tables, the nullable ScanRun assignment FK and extended PostgreSQL guards. Migration 0321 adds SSO identity and Product grant tables. These migrations make no Finding table change and perform no bulk Finding or observation backfill.

Deploy using the existing migration Job. Coordinate an ordinary rollout so older workers cannot consume new assigned deliveries. For application rollback, return the effective strategy to Default, remove overrides that opt into new assignments, drain pending assigned ScanRuns with compatible workers and disable OIDC. A schema downgrade of 0320 rejects a database with assigned ScanRuns because dropping their assignment would invalidate the legacy Test association. Use a pre-upgrade snapshot if the operational plan calls for schema rollback. A restore with SSO disabled preserves identity and grant data for subsequent deployment.

The ordinary nullable index build and trigger replacement need the normal migration lock window. WAL and traffic impact under a production-sized ScanRun corpus were not measured.

An isolated upgrade from 0319 to 0321 and downgrade back to 0319 preserved the legacy completed ScanRun, Test and observation. The reverse SQL rejected a restored database with assigned Engagements. [Migration rehearsal](raw/migration-rehearsal.json)
