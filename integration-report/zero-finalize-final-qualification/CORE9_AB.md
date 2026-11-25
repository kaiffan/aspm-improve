# Core9 A/B

| Concurrency | A p95 / RPS | B p95 / RPS | Повторов на вариант в плане |
|---:|---|---|---:|
| 1 | — | — | 1 |
| 5 | — | — | 1 |
| 10 | — | — | 1 |
| 15 | — | — | 3 |
| 25 | — | — | 3 |

Полный Core9 не запускался. Доступная ARM64 площадка не прошла disk preflight. Замены числами другого SHA нет.

Маршруты и веса сохранены. Findings 30, filtered Product 15, Finding detail 10, Products 10, Tests 10, Engagements 5, Dashboard 10, web Products 5, Endpoints 5. Драйвер проверяет HTTP и shape ответа, архивирует сырые запросы и метрики.

[Маршруты и веса](native/frozen/core9-plan.json) · [Disk gate](STORAGE_CAPACITY.md)
