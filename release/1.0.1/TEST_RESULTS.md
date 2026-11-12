> RC2: см. [RC2_TEST_RESULTS.md](RC2_TEST_RESULTS.md). Ниже сохранён исторический отчёт RC1; его цифры/открытые дефекты не подменяют новую проверку.

# Release validation — ASPM 1.0.1 RC1

Application `5cdbc77fc9d4b8d0899069f5d44cd5241b2acae6`; source/image/dependency evidence in measurements. Tests ran on a separate PostgreSQL test stack or the named validation copy, never against the original million with a test runner.

| Gate | Result | Evidence |
|---|---|---|
| Selected Django R1–5/UI/announcement/authorization suite | 189 pass / 8 skip / 0 fail; 197 total | measurements/tests-final.log |
| Theme bootstrap/storage/System/Chart proxy/Tagulous | 9 pass | measurements/theme-unit.log |
| Runtime Python lint (pinned Ruff0.16.10) | pass | measurements/lint.log |
| Django check / migration drift / OpenAPI generation | pass, inherited local config warnings | measurements/django-checks.log |
| R5/RC compatibility | 104 pairs, 0 mismatch:76 complete JSON +28 HTML/context/table semantic pairs | measurements/compatibility-final.json |
| Opt-in FAST, Product count/none, filtering/ordering/permissions | included in suite/profiles; unchanged standard API | same evidence + test logs |
| Real rollback R5→RC on the same copy |18 full JSON pairs equal; both healthy | measurements/rollback-check.json |
| Main browser pages/themes |50 navigation states,12 functional checks, no JS errors/overflow/failed assets | measurements/browser-validation.json |
| Accessibility |48 authenticated states +4 anonymous login states,0 axe A/AA/2.1AA violations in tested views | browser-validation.json + browser-interactions.json |
| Filter/pagination/dropdown/modal/CVSS/navigation |6 interaction checks +4 anonymous axe checks pass | measurements/browser-interactions.json |
| Real create/edit/login/visibility |5 checks pass; finding1000293; separate access-free user | measurements/browser-write-checks.json |
| Multiple vulnerability references |2 related identifiers, list/detail equal | measurements/live-final.json |
| Real ZAP import/reimport/duplicates |3×201, dedup complete;44 primary/4 closed/40 peer duplicates | import-smoke.json + import-verification.json |
| Reads overlapping import |300 requests c5, all200; separate smoke, not primary A/B | measurements/import-read.json |
| HTTP performance |10 680 completed measured requests,0 errors; interrupted initial probe excluded | benchmark_results.json + raw |
| Source/seed/validation original rows |all1 000 168 original rows equal by row hash/count/sum; main total unchanged | measurements/data-integrity-final.json |
| Exact source/compiled locales/DEBUG=false |verified against running image | source-verification.json + environment.json |
| Rebuild identity/RC image tags |same app/nginx/translation hashes in repeated builds | reproducibility.json + release-images.json |

## Explicit limitations and observed retries

The8 skips are inherited:2 dashboard fixtures await legacy-authorization re-baselining;6 old Endpoint tests are skipped with V3 Locations enabled. The active authorization queries and actual no-access account were tested. This is not a full execution of every DefectDojo test module or a WCAG/cross-browser certification.

Default UI severity-only ordering has ties and one ID overlapped adjacent tested pages in both frozen R5 and RC. No silent order change was made. Navigation smoke with explicit title order on unique fixture titles passes; it does not establish universal title uniqueness. This inherited issue blocks a stable pagination guarantee.

The inherited UI denial handler returns HTTP400 with a403 page; API detail returns403/404 and API lists/forged scope are restricted. No permission weakening was made. The UI promo on denial was found through the access-free account and removed; API error shape retained.

CodeMirror requires its editor API to update the backing textarea; DOM-only fill caused the first create automation attempt to fail validation. Actual native form submission subsequently created one finding, and the harness resumed it instead of generating duplicates. Upstream title capitalization is preserved and accounted for. Successful edit was checked through API as an actual value change.

An initial scan probe reached201 but async dedup timed out because the dedicated worker's prefetch env was empty. The isolated queue was drained after fixing the worker recipe;40 probe rows are retained only in the copy. The subsequent healthy cycle is measured separately. No failed probe was presented as a successful import timing. The normal copy dedup flag was restoredFalse.

A laptop sleep interrupted one early load window; its TimeoutError and monitor stop remain in raw/interrupted-window and are excluded. Initial API-only browser gateway/static404 and one not-ready502 probe are diagnostic artifacts, not final browser benchmarks. Final32 serial browser timings all200. Per-DB counters for the first final Original run were omitted due monitor scope; HTTP/CPU/RSS remain valid.

Local default secret/encryption-key/ALLOWED_HOSTS warnings were not hidden or silently rotated. Production config, TLS, HA/AMD64, external integrations and long-duration20M capacity remain outside this certification. No database or index was deleted, no destructive migration was run, and no external email was sent (copy mail transport locmem).
