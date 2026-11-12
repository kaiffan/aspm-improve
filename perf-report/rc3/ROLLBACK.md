# RC3 rollback

No new index, schema migration, denormalized counter or dependency is introduced.
Do not migrate backwards, drop a database, delete a volume or force-push a release
branch. Release-gate fixes, the test fixture correction and performance changes
are separate commits; the unsuccessful Dashboard experiment is explicitly reverted.

## Images and application

1. Stop the candidate worker after checking active/reserved/scheduled tasks and
   the queue. Keep its broker and data. Do not discard unacknowledged work.
2. Point app and gateway at the recorded RC2 images in
   `release/1.0.1/rc2/build.json`, variant `rc2`. Runtime source:
   `25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb`; application image ID:
   `sha256:40ccfda81142aa8482d0b05fb501684c3bc23df231169a069a02e1da51052f0c`.
3. Recreate only app/gateway services and refresh nginx's upstream DNS. Use the
   same database, media volume, credentials, dependencies and 4×4 uWSGI settings.
   Do not run an initializer or migrations as part of rollback.
4. Check login, permission denial, full Products, Findings first/next/deep pages,
   Dashboard counts, evidence and reports. Compare the same data and identities.
5. Restore the worker on the chosen release after those checks. A return to RC3
   uses the immutable app/gateway tags and IDs in `raw/build-final.json`.

`raw/rollback-check.json` records the actual RC2→RC3 image switch on the isolated
write copy and 18 complete JSON comparisons. The source and protected seed are
checked again afterwards in `raw/integrity-final.json`.

## Code and data

The authorization fix can be reverted independently (`8492b41e23fa4cdb71391c4712e08124f0172289`).
The UI page/autocomplete fix and its safety guards form one rollback unit:
`f21b611ef4888533dfd2252a0c59ed254ae68e67`,
`49066c037bc38a3795cad00ded7dd95f2fd16c96`, and
`6c2e69590c68879e12610f8dcb7c8eb3f700a348`, and
`ccfd52d372695176485e65000b4270e01d7dfb1b`. Revert newest first, or deploy the
recorded RC2 images. Neither performance change alters stored data.
Reverting the release-gate commit `b2d79aa1e78aee6a555e307830732ac73a2705cf`
restores both import blockers and must block promotion again.

TruffleHog's default Hash Code configuration is unchanged. The restored upstream
v3 helper populates an additive stable unique ID. Sites using Unique ID from tool
must review existing imports before changing their dedup algorithm or enabling
folding. No mass recomputation or dedup migration is performed by this release.
An older runtime can read the same schema; an image rollback does not erase
unique IDs already written by a parser. Keep database backups and do not rewrite
customer findings as part of application rollback.

All writes in this verification use `aspm_rc3_validation` and its independent
media volume. The original database and `dd_round4_seed` are never used for write
tests. Audit/test/validation databases and volumes are retained for inspection.
