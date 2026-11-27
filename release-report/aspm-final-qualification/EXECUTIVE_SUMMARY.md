# ASPM 1.0.1 · локальная квалификация

**STAGING CANDIDATE · PRODUCTION HOLD**

Ревизия приложения для staging `e2f3f244f478033f5137ccb1248ab9c3b5d577df`. Чарт Helm `0.1.0-rc.11`. [Решение по выпуску](RELEASE_GATE.md) · [Git-интеграция](GIT_INTEGRATION_REPORT.md)

| Направление | Наблюдение |
|---|---|
| Инвентаризация | 896 записей URL resolver, 857 уникальных выражений путей, 389 уникальных обработчиков. Из них 509 записи в ветке /api/. DRF сообщил 824 сопоставлений HTTP-методов с действиями. |
| Браузер | Chromium 158.0.8127.88, 147 зарегистрированных переходов, 140 PASS, 0 FAIL, 16 снимков. [Действия](UI_INTERACTION_COVERAGE.md) |
| Scanner E2E | 6/6 форматов, 55 HTTP-запросов, 2 завершённых версий отчёта. [Форматы](SCANNER_COMPATIBILITY.md) |
| JavaScript | 17 PASS |
| Helm | 23 PASS, lint семи профилей, пакет чарта и серверный dry run |
| Django | 8 349 PASS · 562 SKIPPED · 0 FAIL. [Регрессия](FINAL_REGRESSION.md) |
| S3 | 9 тестов за 12.234 с · OK. Обнаружено по группам: 9 на отдельном MinIO с HTTPS и versioning |
| Восстановление | 8 оригиналов с идентичным SHA-256 и идентичные выборки ScanRun |
| Переносимость | Независимый локальный клон, ARM64-сборка двух образов и push/pull по digest через loopback registry |
| Открытые условия | HA 2/3/1 не прошло из-за памяти узла. Остаются системные CVE без исправленных версий в базе сканера и замечания полного Ruff. [Безопасность](SECURITY_REPORT.md) |

[Реестр дефектов](DEFECT_REGISTER.md) · [Развёртывание на другом ПК](DEPLOYMENT_ON_NEW_PC.md) · [Ограничения](KNOWN_LIMITATIONS.md)
