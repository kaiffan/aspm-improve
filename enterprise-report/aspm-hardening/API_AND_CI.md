# ASPM API and CI/CD

The scanner upload route is `POST /api/aspm/v1/scans/`. Use a repository-scoped service token with `submit`, `status`, `read` and, when needed, `reports`. Read the token from a masked CI variable. The body is multipart with the project and repository IDs, full commit SHA, scanner type, delivery key, and file. Use a stable delivery key for CI retries so a retry represents the same scan.

```sh
curl --fail-with-body --silent --show-error \
  -H "Authorization: ASPM ${ASPM_CI_TOKEN}" \
  -F "project_id=${ASPM_PROJECT_ID}" \
  -F "repository_id=${ASPM_REPOSITORY_ID}" \
  -F "commit_sha=${CI_COMMIT_SHA}" \
  -F 'scanner_type=Generic Findings Import' \
  -F "idempotency_key=${CI_PIPELINE_ID}/${CI_JOB_ID}" \
  -F "pipeline_id=${CI_PIPELINE_ID}" \
  -F 'file=@findings.json;type=application/json' \
  "${ASPM_URL}/api/aspm/v1/scans/"
```

New scans return 202 and the scan ID. An exact replay returns 200 and the existing scan. A mismatching reuse returns 409. Poll `GET /api/aspm/v1/scans/{scan_id}/` with backoff and honor `Retry-After`. The service token limit defaults to 120 requests/minute including status polling. Check `COMPLETED` before using observations and treat `FAILED` as an explicit error. A completed scan does not imply that every expected scan ran. The original is authorized separately at `GET /api/aspm/v1/scans/{scan_id}/artifact/`.

To generate an immutable report, send `POST /api/aspm/v1/commits/{commit_id}/reports/` and poll the report list. Use `GET /api/aspm/v1/reports/{report_id}/download/?format=json` or `format=html` after completion. The request may select a pipeline or explicit scan IDs. Finalize is optional. Webhook recipients verify the timestamp and signature and deduplicate the stable event ID. See [WEBHOOK_EVENTS.md](WEBHOOK_EVENTS.md) and [WEBHOOK_SECURITY.md](WEBHOOK_SECURITY.md).
