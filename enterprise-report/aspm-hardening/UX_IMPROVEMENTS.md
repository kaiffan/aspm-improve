# UX improvements

Added webhook administration in the existing shell with explicit empty states, safe error codes, validation/success feedback, bounded lists and visible attempt/replay state. Integration breadcrumbs reset through the existing breadcrumb utility. Inline breadcrumb links are underlined. Scrollable evidence/delivery tables have accessible region labels and keyboard focus. Mobile tables remain horizontally scrollable within their region without overflowing the page.

Commit evidence adds Copy SHA with explicit copy success/failure feedback and a clear explanation that historical observations do not change when live Findings are edited. It keeps pending/failed ScanRuns and incomplete/unknown coverage visible, does not introduce a false security score and does not reinstate finalize or manual UI scan upload. Corrected the scanner empty-state colspan. Live refresh and bounded server-side selections are retained.

The global permission page now returns HTTP 403; affected tests were updated only for explicit denial assertions, retaining object isolation and no-data-leak checks. No DRF ingestion contract was changed.
