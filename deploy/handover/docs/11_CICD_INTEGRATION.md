# 11 | Интеграция CI/CD

POST `/api/aspm/v1/scans/` с `Authorization: ASPM <token>`, multipart `file`, `scanner_type`, `project_id`, `repository_id` или `repository_url`, полный `commit_sha` и заголовок `Idempotency-Key`. Для трассировки заполните `pipeline_id`, `job_id`, `scanner_version`, `expected_scanners` и поля политики Engagement. Храните токен в secret store CI.

| Формат | Точное имя типа |
|---|---|
| Dependency-Track FPF JSON | `Dependency Track Finding Packaging Format (FPF) Export` |
| Semgrep JSON | `Semgrep JSON Report` |
| Trivy JSON schema 2 | `Trivy Scan` |
| KICS JSON | `KICS Scan` |
| Fortify XML | `Fortify Scan` |
| ffuf JSON | `ffuf Scan` |

Поллинг `GET /api/aspm/v1/scans/<uuid>/` до COMPLETED/FAILED. HTTP 202 подтверждает приём, 200 при повторе возвращает тот же ID. Повторяйте тот же ключ и payload после timeout/429/5xx, учитывая Retry-After. Новый ключ для нового запуска. HTTP 400 требует проверки полей, 401/403 — scopes и срока, 409 — сравнения исходного payload и SHA. Для FAILED проверьте `error_code`. После устранения причины POST `/api/aspm/v1/scans/<uuid>/retry/` с правом submit.

Один POST регистрирует запуск, результаты публикуются после processing. Для выгрузки запрашивайте `POST /api/aspm/v1/commits/<id>/reports/` с `{}`, `pipeline` или `scan_ids`. Статус версий приходит с GET того же маршрута. Скачивание `/api/aspm/v1/reports/<uuid>/download/?format=html` либо json. Оригинал — `/api/aspm/v1/scans/<uuid>/artifact/`. Сверяйте `artifact_sha256` и `checksums` отчёта. Deprecated finalize сохранён для legacy.

[Скрипт и примеры](../integration-examples/README.md) · [Матрица совместимости](../qualification/SCANNER_COMPATIBILITY.md)
