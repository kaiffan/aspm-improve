# System and provenance audit

RC2 remote release ref was verified before edits at full SHA
`9384826c2c2ccdbf0178ebc3faa5ea3e5513473d`; runtime source is
`25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb`. The original feature checkout and
uncommitted user files were not edited. Work is on a separate release-based
worktree/branch, as explicitly requested for this fork.

Accepted RC3 runtime `ccfd52d372695176485e65000b4270e01d7dfb1b`; app `sha256:f552dff5e34845dc60a8d4dcb33c488974795ceeff9e55076fb76a06d4799bac`;
gateway `sha256:d3f598c79766b93076cbb1da0402cdee0a745c108379add973a2bcfd243c9e5c`. Both builds use the checked-in immutable
dependency image digest lock, GNU msgfmt and Git archive. No application library
update or frontend asset change. Full dependency versions: `raw/environment.json`.
Runtime file/image verification: `raw/provenance.json`.

Docker: 10 logical CPUs,
7.816 GiB VM RAM,
aarch64, OrbStack,
engine 29.8.2. No per-container CPU/memory
limits; DEBUG=False; CONN_MAX_AGE=0.
uWSGI 4 processes ×4 threads. Original demo/worker were stopped for both builds.
Power, host free memory, swap, OOM and all relevant containers were sampled.
Baseline host swap snapshot: `total = 1024.00M  used = 236.69M  free = 787.31M  (encrypted)`. This differs from
historical snapshots and is another reason not to reuse historical Round 5/RC1
performance numbers. Current A/B uses the same host conditions and guards.

PostgreSQL 18.6, shared_buffers 128 MiB, work_mem 4 MiB,
default_statistics_target 100, max_connections 100, max_parallel_workers_per_gather
2, JIT on. The primary server has empty shared_preload_libraries and IO timing off.
Its settings/statistics are not changed. The separate SQL-audit copy enables
pg_stat_statements and IO timing, restores identical rows, ANALYZEs once before
either build and retains the same audit statistics for both. Its timings are
explicitly separate from primary HTTP measurements.

Integrity includes every Finding field, count, ID sum, full-row XOR, max_updated
and SHA-256 over ordered row SHA-256 values. Source and seed match before and after:
`1d6189a4404e3a19c18b17f891a358dadc97e53a3de76c955ab4a04690d3db87`.
No destructive migrations, DROP, volume deletion, source write tests or force push.
