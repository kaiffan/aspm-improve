# Безопасность

## Strict API-only

52/52 теста прошли при ASPM_TEST_API_ONLY=True. Human/session/обычный DD token не получает ASPM submit/retry/finalize/reports scopes. Legacy human UI import/reimport даёт 404, legacy API human upload — 403. Новый browser export создаёт только GeneratedReport и требует Product edit, POST, CSRF.

## Product / repository RBAC

Backend проверяет Commit overview/state, scanner history, historical findings, comparison, generated reports и downloads. Foreign Commit/Product/pending ScanRun selectors отвергаются. Scoped CI tokens сохраняют product/repository/user boundaries, expiry/revocation, digest storage, PostgreSQL rate limiter, streaming file validation и SHA/size integrity.

## Исторические данные и скачивание

Оригиналы остаются private, immutable и защищены существующими storage checks. Protected FileResponse сохраняет attachment, no-store, nosniff, sandbox CSP. Generated HTML экранирует scanner text. Завершённые ScanRuns, observations, reports и FK membership защищены PostgreSQL triggers.

## Реальные проверки

HTTP + Celery flow прошёл на immutable image; unauthorized report download дал 401, upload чужого Product — 403, unknown coverage не стала complete. Browser проверил все пять вкладок, 0 file inputs, bounded polling script и FAILED history. Старые report bytes/hash сохранились после позднего Semgrep.

[52 strict tests](checks/test-results.json), [HTTP](checks/image-http-smoke.json), [browser](checks/browser-smoke.json), [image blobs](checks/image-provenance.json), [защищённый 1M seed](checks/protected-seed-fingerprint.json), [protected source](protected-source-fingerprints.json). Seed сравнивается с прежним integrity reference; это не использование старых performance measurements.
