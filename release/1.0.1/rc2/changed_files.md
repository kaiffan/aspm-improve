# RC2 changed files

All runtime changes are independent commits after RC1. Frozen app source is25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb; later QA/docs do not change the image source.

| Component | Files | Purpose |
|---|---|---|
| UI pagination | dojo/utils.py; unittests/test_ui_pagination_hardening.py | Stable tie ordering, safe page sizes,9 behavioral guards |
| Product filters | dojo/templates/dojo/filter_snippet.html; unittests/test_rc2_product_filters.py; browser/rc2_regression.cjs | Native Clear navigation,6 scope/filter guards, real red/green browser proof |
| Finding API pagination | dojo/finding/api/large_offset_pagination.py; unittests/test_finding_pagination_collections.py | Standard list fallback,2 guards; FAST ORM preserved |
| Select2 accessibility | dojo/static/dojo/js/aspm.js; release/1.0.1/scripts/theme.test.cjs | Existing labels on late widgets;3 new Node cases |
| Metadata/build | dojo/aspm/branding.py; dojo/aspm/release.json; dojo/settings/settings.dist.py; release/1.0.1/scripts/build_images.py; unittests/test_aspm_release_ui.py | RC2 source/build timestamp, unchanged upstream version |
| Test isolation/portability | unittests/test_tag_inheritance_perf.py; unittests/test_jira_config_product.py | Debounce fixture isolation without changing counts; offline DNS matcher |
| QA/evidence | release/1.0.1/rc2/scripts,raw,diagnostics,excluded,charts,screenshots; profile/plans JSON | Reproducible new controlled series and all corrections/exclusions |
| Release | Six RC2 reports plus RELEASE_NOTES/CHANGELOG/BUILD/DEPLOY/ROLLBACK | Gated candidate status, provenance and safe rollback |

Exact machine-readable path list: [changed_files.json](changed_files.json). Existing source/seed databases, user feature branch and its untracked files were not overwritten.
