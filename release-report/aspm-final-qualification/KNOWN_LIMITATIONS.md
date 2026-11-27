# Открытые условия

- Single-node OrbStack Linux/ARM64 с другими активными проектами. Multi-node HA, отсутствие разрыва пользовательских сессий и серия rolling updates остаются открыты.
- Corporate PostgreSQL, S3, Keycloak/AD, Prometheus, VictoriaMetrics, Grafana, RPO/RTO, IAM, TLS и образ native AMD64 требуют отдельной квалификации.
- Расширенное покрытие Firefox и WebKit, живой Keycloak Expert/revocation, полное ручное WCAG покрытие и несколько административных сценариев остаются NOT TESTED. Короткий browser smoke: Firefox 144.0.2 PASS, WebKit 26.0 PASS.
- Core9/Acceptance на 1M, soak, matched A/B, storage latency и monitoring overhead не измерены.
- Полный проверенный набор сценариев для Fortify FPR, Semgrep SARIF и корпоративного обозначения FF остаётся открытым.
- Остаются замечания полного Ruff и системных пакетов Debian. Результаты сканов и сведения об исправленных зависимостях приведены в [отчёте по безопасности](SECURITY_REPORT.md).
