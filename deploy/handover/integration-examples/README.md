# Интеграция из pipeline

Примеры получают уже созданный отчёт сканера. Сохраните структуру оригинального отчёта и расширение. Выполняйте отправку по HTTPS, с отдельным scope-токеном на проект/репозиторий. Для повторной отправки после временного сбоя сохраните те же bytes и ключ.

```bash
export ASPM_URL=https://aspm.example.invalid ASPM_PROJECT_ID=123 ASPM_REPOSITORY_ID=456
export ASPM_COMMIT_SHA="$(git rev-parse HEAD)" ASPM_IDEMPOTENCY_KEY="pipeline-123/semgrep/1"
# ASPM_TOKEN доступен как защищённая CI variable.
integration-examples/curl/upload.sh 'Semgrep JSON Report' semgrep.json
```

Результат сохраняйте как ScanRun ID, в логи CI достаточно ID, status и checksum. После COMPLETED откройте commit evidence. [Точные типы](scanners/FORMATS.md) · [GitLab CI](gitlab-ci/aspm.yml) · [GitHub Actions](github-actions/aspm.yml) · [API](../docs/11_CICD_INTEGRATION.md)
