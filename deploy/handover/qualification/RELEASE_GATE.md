# Release gates | ASPM 1.0.1

**Текущий кандидат rc.11 · PRODUCTION HOLD.** Результаты S3/DR и открытые проверки перечислены в [квалификации rc.11](FINAL_STORAGE.md).

## История предыдущей поставки


| Gate | Статус | Основание |
|---|---|---|
| HANDOVER PACKAGE READY | PASS | Переносимый архив, два SBOM, SHA-256, проверенная документация и lab scripts |
| LOCAL QUALIFICATION | PASS | Django 8 357, strict 86, JS 17, Helm 20, Chromium 240 + 11 проверок |
| CLEAN INSTALL | PASS WITH RECOVERY | Исходно пустая DB. Первая попытка migration Job завершилась при восстановлении PostgreSQL, повтор прошёл |
| ARM64 BUILD | PASS | Оба release images собраны и запущены с точной маркировкой SHA |
| AMD64 BUILD | NOT TESTED | Native Linux/AMD64 runner недоступен. Включён build workflow |
| CORPORATE STAGING | NOT TESTED | Параметры кластера, registry, DB/CSI и TLS не предоставлены |
| CORPORATE KEYCLOAK/AD | NOT TESTED | Требуется фактический IdP и тестовые AD группы |
| PERFORMANCE 1M | NOT TESTED | Требуется подходящий native стенд и согласованный снимок |
| MULTI-NODE HA | NOT TESTED | В лаборатории один узел |
| PRODUCTION READINESS | HOLD | Open security findings, внешние gates и решение владельца |

[Полные результаты](TEST_MATRIX.md) · [Security](SECURITY_REPORT.md) · [Параметры владельца](../checklists/INFRASTRUCTURE_INPUT.md)
