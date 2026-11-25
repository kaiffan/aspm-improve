# Architecture review

Baseline application: `25da29aaff229d3a815e223d8af8bdc4ecca7c5e`; qualification-only HEAD: `1ed9e9f396e11314514d58176db43af805e128ec`. Both contain origin/dev. All four user-supplied commits exist. Changes are isolated on feature/aspm-enterprise-hardening. The original checkout's untracked files and release branches were preserved.

Runtime is Django/uWSGI with nginx static assets, Celery workers and Celery beat. Existing IngestionJob is retained until business completion, not broker acknowledgement. Its dispatcher uses skip-locked batches and session advisory locks fence work. Webhook recovery is invoked by that same dispatcher; there is no extra dispatcher deployment. Broker/cache are separate connections. Data is PostgreSQL-authoritative; a filesystem path is a private evidence key, not a public media URL.

The repository's helm/defectdojo chart advertises 3.6.0-dev and includes bundled database dependencies. It was used as a runtime reference, not copied as an ASPM release contract. The new independent chart has no dependency subcharts and requires external services and shared persistent claims. Core ingestion, deduplication, observations and API-only policy remain in their existing modules. No domain reorganization or SSO replacement was attempted.
