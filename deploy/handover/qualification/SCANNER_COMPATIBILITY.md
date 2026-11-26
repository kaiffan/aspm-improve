# Совместимость сканеров

| Scanner / формат | Exact scan type | Fixture | Findings E2E |
|---|---|---|---:|
| Dependency-Track FPF JSON | Dependency Track Finding Packaging Format (FPF) Export | dependency_track/one_finding.json | 1 |
| Semgrep JSON | Semgrep JSON Report | semgrep/one_finding.json | 1 |
| Trivy JSON schema 2 | Trivy Scan | trivy/scheme_2_many_vulns.json | 5 |
| KICS JSON | KICS Scan | kics/many_findings.json | 18 |
| Fortify XML | Fortify Scan | fortify/fortify_few_findings.xml | 2 |
| ffuf JSON | ffuf Scan | ffuf/ffuf_one_vuln.json | 1 |
| Semgrep SARIF | SARIF | Semgrep OWASP benchmark | Parser-only |
| Fortify FPR | Fortify Scan / Fortify Scan v2 | Audit state и source lines | Parser-only |
| Корпоративный FF | UNCONFIRMED | Требуется название и очищенный образец | — |

Live сценарий проверяет multipart API, COMPLETED, ненулевой severity summary, idempotent replay, SHA-256 оригинала и отказ скачивания для чужого scope. HTML и JSON отчёты проверяются на одном commit из шести завершённых сканов. Отдельные parser tests покрывают CWE/CVE, fixed versions, dedup и метаданные. Fixture закрепляет проверенный вариант формата. Версии корпоративных раннеров и их варианты export остаются отдельной проверкой. Fortify filename .xml выбирает соответствующий parser. [Интеграция](../docs/11_CICD_INTEGRATION.md)
