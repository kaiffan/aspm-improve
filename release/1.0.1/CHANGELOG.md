# ASPM 1.0.1 RC2

- Restore native Clear navigation without changing Product filtering or permissions.
- Preserve primary UI ordering with a PK tie-break; bound user page size and recover malformed values.
- Use standard DRF pagination for collection/delete-preview lists; retain opt-in FAST ORM path.
- Label late-initialized Select2 combobox/search controls from existing labels.
- Isolate the test-only grade cache marker; keep exact query assertions unchanged; make offline Jira DNS failure matching portable.
- Freeze source/build metadata and repeat controlled R5/RC1/RC2 benchmarks and real browser/import/rollback checks. Formal promotion blocked by two inherited loader errors.

The RC1 changelog below is historical.

# Changelog ASPM 1.0.1 RC1

- Added: shared OTP-derived design tokens without the excluded light-blue accent; original ASPM SVG identity and replaceable branding.
- Added: Light/Dark/System with persistent browser preference, live chart colors, accessible mobile shell and focus behavior.
- Improved: Dashboard hierarchy/numeric formatting, dense tables, form/editor/filter/report/login themes, page-size menu positioning, accessible names/contrast and asynchronous Tagulous labeling.
- Removed from UI: commercial purchase/PAYG/Pro menus, promotional OS/star/error/long-request banners. Operator/read-only messages and upstream legal attribution retained.
- Added: separate product/upstream/source metadata, standalone report generator/cover branding and digest-pinned reproducible app/nginx builds.
- Preserved: all Round1–5 application optimizations and standard API/authorization/import/deduplication behavior. No new migrations/indexes/services/cache layer.
- Verified: repeated HTTP and browser comparisons, real write/import gates, source/translation hashes and real rollback. Known inherited pagination/status limitations remain explicit; no stable production tag.

Measured results and complete scope: RELEASE_NOTES.md, PERFORMANCE.md, TEST_RESULTS.md.
