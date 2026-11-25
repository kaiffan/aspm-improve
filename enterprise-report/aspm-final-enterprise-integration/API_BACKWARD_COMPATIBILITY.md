# Совместимость API v2 и v3

До реализации схемы были выгружены с `0352960ff143b9fd8037f5f72525afe32b29e6fd`. После реализации снова выгружены обе схемы. В каждой версии `cmp` вернул 0. Маршруты, параметры и описания объектов запросов и ответов совпадают побайтно. [SHA-256 схем](dual-raw/openapi-sha256.txt)

| Поверхность API | Проверка |
| --- | --- |
| v2 Product Types, Products, Engagements, Tests | Штатные create и detail, после Keycloak входа проверен доступ по роли |
| v2 Findings | Создание, PATCH статуса и False Positive, фиксация предыдущих исторических наблюдений |
| v2 Import Scan и Reimport Scan | Штатный DRF-токен без ASPM enrollment, оба запроса без Git вернули HTTP 201, импорт за границей Product вернул HTTP 403 |
| v3 Assets, Engagements, Tests, Findings | Схема, существующие модульные проверки и запреты для чужого Product |
| v3 Import | Импорт в существующий Engagement без SCM, HTTP 200 с Keycloak-сессией EXPERT и со штатным DRF-токеном |
| Нативная отчётность | Штатные маршруты и разрешения Product, Engagement и Test, проверка HTML |
| ASPM v1 | Отдельный scoped token, commit upload, ScanRun, оригиналы и версии Generated Reports |

Классические integrations используют принадлежащие им Products, Engagements или Tests согласно штатным правам. Защита DevSecOps endpoint по Product/Repository scope сохранена. Проверка RC5 для конкурентного PATCH/reimport проходит через обычный протокол записи Finding. [Результаты сервисного токена](dual-raw/native-machine.json) · [Матрица проверок](CLASSIC_AND_DEVSECOPS_REGRESSION.md)
