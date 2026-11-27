# Решение о выпуске

**STAGING CANDIDATE · PRODUCTION HOLD**

Владелец согласовал публикацию `master` для тестового развёртывания. Ревизия исходников образов `e2f3f244f478033f5137ccb1248ab9c3b5d577df`. Чарт Helm `0.1.0-rc.11`.

| Gate | Состояние |
|---|---|
| Functional, Classic, DevSecOps | PARTIAL. 6/6 форматов, 55 HTTP-запросов, 2 завершённых версий отчёта. Полный сценарный охват не достигнут |
| UI/UX | PARTIAL. Chromium 158.0.8127.88, 147 зарегистрированных переходов, 140 PASS, 0 FAIL, 16 снимков. Остались дополнительные роли и findings axe |
| Security | STAGING. CVE-2026-6653 и девять Python-находок устранены. Trivy показал 0 CRITICAL и 0 секретов для пары образов. Для 56 оставшихся HIGH в системных пакетах Debian база сканера не указывает исправлений. [Безопасность](SECURITY_REPORT.md) |
| Concurrency | 111 тестов за 30.468 с · OK. Обнаружено по группам: 111 |
| Storage | PARTIAL. MinIO tests PASS, FS restore PASS в малом масштабе |
| Kubernetes | PARTIAL. 1 web, 1 worker и 1 Beat достигли Ready. Helm HTTP smoke завершился. Нагрузочный HA gate открыт. Multi-node HA остаётся открытым |
| Monitoring | PARTIAL. Prometheus → VictoriaMetrics → Grafana подтверждено. ASPMWebScrapeUnavailable подтвердил firing и resolve. |
| Full Django | PASS · 8 349 PASS, 562 SKIPPED, 0 FAIL |
| JS, Helm | PASS. 17 и 23 проверки соответственно |
| Clean install | PASS для локального ARM64. Чистая PostgreSQL, миграции, Compose preflight, HTTP и API, публикация пары образов в loopback registry. [Репетиция](CLEAN_INSTALL_REHEARSAL.md) |
| Ruff | FAIL на всём дереве. 21 600 результатов первоначального полного lint, 485 результатов в приложении, тестах и handover |
| Handover ready | Инструкции сборки и развёртывания staging из Git используют SHA из манифеста. [Начало работы](../../deploy/handover/START_HERE.md) |
| Master и post-push | Fast-forward исходного `716efb4633`. [Проверка SHA после публикации](MASTER_PUSH_VERIFICATION.md) |
| Production | HOLD. Корпоративный контур и условия нагрузки открыты |

Внешние зависимости и полная 1M квалификация перечислены в [KNOWN_LIMITATIONS](KNOWN_LIMITATIONS.md). Любая публикация master должна использовать SHA квалифицированного дерева и не запускать production rollout.
