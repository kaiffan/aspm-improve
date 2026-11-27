# Scanner compatibility

Проверка использовала один синтетический commit. Каждый принятый файл прошёл HTTP API, outbox, Celery, хранение и повторное скачивание. После всех сканов созданы HTML и JSON отчёты. 6/6 форматов, 55 HTTP-запросов, 2 завершённых версий отчёта.

| Scan Type | Fixture | Приём и replay | Findings | Другой Product | Итог |
|---|---|---|---:|---:|---|
| Dependency Track Finding Packaging Format (FPF) Export | `dependency_track/one_finding.json` | 202 / 200 | 1 | 404 | PASS |
| Semgrep JSON Report | `semgrep/one_finding.json` | 202 / 200 | 1 | 404 | PASS |
| Trivy Scan | `trivy/scheme_2_many_vulns.json` | 202 / 200 | 5 | 404 | PASS |
| KICS Scan | `kics/many_findings.json` | 202 / 200 | 18 | 404 | PASS |
| Fortify Scan | `fortify/fortify_few_findings.xml` | 202 / 200 | 2 | 404 | PASS |
| ffuf Scan | `ffuf/ffuf_one_vuln.json` | 202 / 200 | 1 | 404 | PASS |

Semgrep SARIF и Fortify FPR остались открыты как end-to-end сценарии. Авторизация и безопасные parser fixtures дополняют эту проверку, но не заменяют полный набор 0/1/many, dedup, CWE/CVE и reimport для каждого формата. Корпоративное обозначение FF требует подтверждения владельца.
