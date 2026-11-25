# DefectDojo compatibility

The integration extends the fork's confirmed enterprise candidate and the existing DefectDojo 3.5.100-based application. It keeps the original Product PKs, SCM models, Test/Finding hierarchy, parser factory and importer. Existing scanner identity/dedup settings and RC5 Finding write fencing remain in their original modules.

Default ingestion preserves commit-bound Engagement and per-Run Test creation. Existing local user and machine integrations keep their authentication modes. The managed OIDC role overlay intersects scoped visits with server-side permissions and is disabled by default. Corporate Pro plugin overrides and proprietary scanner formats were outside local verification.
