# Webhook management UI

Configuration → Integrations → Webhooks exposes create/edit, enable/disable, archive, event selection, Product/repository/scanner/severity/status/source/pipeline rules, timeout, attempts and request rate. Configuration validation performs no network send. Test events are queued asynchronously. Delivery/history and attempt pages paginate 25 rows server-side and filter by state; errors are safe codes, not consumer bodies. Replay retains event ID and history. Last success is shown per subscription. Secret generation/rotation displays a no-store one-time page and never a prefilled configuration field.

A centralized platform capability controls navigation and every handler. Product viewers and ordinary staff cannot manage subscriptions. Archived configurations remain addressable for historical review. Explicit permission delegates can administer the platform integration without borrowing the future Expert role. Configuration modifications revoke pending old revisions. Waiting for the periodic dispatcher is visible behavior, not a synchronous delivery claim.

Browser regression covers desktop/mobile, light/dark/system, table geometry, accessibility and create/secret/history/edit/unsafe endpoint rejection plus Copy SHA. See raw/browser.json and screenshots.
