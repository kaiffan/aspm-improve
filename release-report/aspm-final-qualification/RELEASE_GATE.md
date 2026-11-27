# Решение о выпуске

**RELEASE HOLD · MASTER UPDATED NO · PRODUCTION HOLD**

| Gate | Состояние |
|---|---|
| Functional, Classic, DevSecOps | PARTIAL. 6/6 форматов, 55 HTTP-запросов, 2 завершённых версий отчёта. Полный сценарный охват не достигнут |
| UI/UX | PARTIAL. Chromium 158.0.8127.88, 147 зарегистрированных переходов, 140 PASS, 0 FAIL, 16 снимков. Остались дополнительные роли и findings axe |
| Security | HOLD. Trivy отметил CVE-2026-6653 в libxml2 Django-образа. Требуется оценка влияния и ручная проверка унаследованной Git-истории |
| Concurrency | 111 тестов за 30.468 с · OK. Обнаружено по группам: 111 |
| Storage | PARTIAL. MinIO tests PASS, FS restore PASS в малом масштабе |
| Kubernetes | PARTIAL. 1 web, 1 worker и 1 Beat достигли Ready. Helm HTTP smoke завершился. Нагрузочный HA gate открыт. Multi-node HA остаётся открытым |
| Monitoring | PARTIAL. Prometheus → VictoriaMetrics → Grafana подтверждено. ASPMWebScrapeUnavailable подтвердил firing и resolve. |
| Full Django | PASS · 8 349 PASS, 562 SKIPPED, 0 FAIL |
| JS, Helm | PASS. 17 и 23 проверки соответственно |
| Clean install | PARTIAL. Git clone, ARM64 build, local registry, Compose preflight |
| Ruff | FAIL на всём дереве. 21 600 результатов первоначального полного lint, 485 результатов в приложении, тестах и handover |
| Handover ready | HOLD. Инструкции доступны, проверка staging из GitHub открыта |
| Master updated и post-push | HOLD. Ветка согласована, публикация ждёт gates |
| Production | HOLD. Корпоративный контур и условия нагрузки открыты |

Внешние зависимости и полная 1M квалификация перечислены в [KNOWN_LIMITATIONS](KNOWN_LIMITATIONS.md). Любая публикация master должна использовать SHA квалифицированного дерева и не запускать production rollout.
