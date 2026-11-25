# Engagement selection

Open Projects, then Engagement policy for the Product. Repository settings override Product settings. The deployment default is `default`. An accepted delivery keeps its assignment across retries and later policy changes.

| Policy | Assignment for a new delivery |
| --- | --- |
| Default | The worker creates the existing commit-bound Engagement per ScanRun. |
| Repository | Reuse an active binding for the Repository PK. |
| Branch | Reuse a binding for the Repository PK and exact supplied `branch`. A new branch gets its own binding. |
| Environment | Reuse a binding for the Repository PK and exact supplied `environment`. |
| Explicit | Require the ID of an active Engagement and a token with `engagement:select` in addition to `submit`. |

A trusted token can supply `engagement_id` with any policy. The Engagement must belong to the same Product and match the Commit when it is commit-bound. A Repository-scoped token can pick a managed Engagement in that Repository or an Engagement bound to its Commit or canonical SCM URL. A Product-scoped token can select an unbound Engagement in its own Product.

Managed names use the stable Repository ID and optionally the branch or environment. Equal short repository names are valid. An allowed URL change before evidence exists keeps Repository identity when the PK stays the same. Existing evidence guards fence canonical URL changes after runs or scoped tokens exist. A new Repository PK starts a separate scope.

Archiving a binding preserves previously accepted jobs, Tests and history. A later delivery creates a successor. Closing the underlying Engagement retires its managed binding on the next matching delivery. An archival action and policy changes appear in the Product history. The policy page lists the latest assigned Test for each binding.

Per-Repository row locks and a partial unique index serialize initial binding creation. Each accepted scan still owns a distinct Test. Scope and policy changes never move existing Tests or Findings.
