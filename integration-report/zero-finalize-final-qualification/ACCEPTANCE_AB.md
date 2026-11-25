# Acceptance A/B на 1M Findings

| Native operation | Требование p90 | A p90 | B p90 |
|---|---:|---|---|
| Import 400 | ≤110 с | — | — |
| Finding Browser | ≤60 с | — | — |
| Finding POST | ≤5 с | — | — |
| Native HTML Report | ≤70 с | — | — |

Native run ожидает VM. План содержит три независимых восстановления на вариант и 10 browser VU на повтор. Драйвер проверяет 400 Findings на import, ноль duplicates, заполнение Test и ожидаемые HTML строки. В конце повтора проверяются 40 100 новых Findings, 100 импортов и не менее 120 000 записей импортированного evidence. Порог сверяется для каждого повтора. Метрика нового scanner upload измеряется отдельно.

[Зафиксированный драйвер](native/frozen/mixed.cjs)
