# ASPM 1.0.1 RC2 — release gates

**Статус: кандидат подготовлен, формальный release gate не пройден.**

| Gate | Result |
|---|---|
| Product-фильтр, reset/navigation, scopes | PASS |
| UI pagination boundaries/count/order | PASS |
| RBAC/Product membership/no foreign data | PASS |
| Все обязательные и доступные Django tests | BLOCKED: 2 inherited import errors; 8111 pass, 553 skip |
| Import/reimport/dedup на write-copy | PASS |
| R1–5 guards/API compatibility | PASS |
| Контролируемая performance-серия | PASS: нет доказанной существенной регрессии; разброс опубликован |
| Image source/static/dependencies/provenance | PASS |
| Light/Dark/System / real browser | PASS |
| Release notes/rollback | UPDATED |
| Основная БД1 000 168 и seed целы | PASS |
| Known limitations | DOCUMENTED |
| Promote aspm:1.0.1-rc2 / Stable | NOT PERFORMED |

Два errors нельзя заменять skips/stubs. После их корректного устранения повторить full suite, соответствующие guards и provenance; только затем promote immutable alias по content ID. Stable1.0.1 отдельно не публиковать без приёмки.
