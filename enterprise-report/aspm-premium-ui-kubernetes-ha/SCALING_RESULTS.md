# Измерения масштабирования

Шесть параллельных HTTP клиентов в течение 14 секунд вращали Projects, Reports, API v2 products и CSS. Одновременно отправлялись девять простых синтетических scanner reports. Подключения измерены через pg_stat_activity, CPU и memory взяты одномоментным Docker stats. Это малый одиночный прогон каждого профиля во время работы других изолированных тестов на той же машине.

| Профиль | HTTP RPS | HTTP p95 | Scan completions / s | Median acceptance | Median queue wait | PG active / total | PG CPU / RAM | Worker RAM на pod |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| 1 web / 1 worker | 84.50 | 139.30 ms | 2.98 | 78.65 ms | 528.37 ms | 1 / 7 | 46.83% / 60.34 MiB | 223.5 MiB |
| 2 / 3, тот же суммарный лимит | 126.71 | 109.34 ms | 3.83 | 255.67 ms | 170.04 ms | 3 / 7 | 78.94% / 62.62 MiB | 230.2–230.7 MiB |
| 2 / 3, обычные лимиты на pod | 126.07 | 102.50 ms | 4.26 | 95.60 ms | 212.67 ms | 1 / 7 | 82.51% / 59.77 MiB | 221.0–222.2 MiB |

HTTP RPS вырос примерно в 1.50× при том же суммарном бюджете. Время принятия upload в этом коротком прогоне увеличилось. Профиль с дополнительным CPU/памятью завершал в 1.43× больше сканов в секунду относительно 1/1. В matched profile лимит web делится пополам, worker делится на три с погрешностью округления 1m CPU и 1MiB памяти. Тесты на стабильную долгую пропускную способность, внешний PostgreSQL и большие датасеты не проводились.

[Результаты HTTP](raw/statistics.json) · [Single resources](raw/bench-single-resources.txt) · [Matched resources](raw/bench-matched-resources.txt) · [Full resources](raw/bench-full-resources.txt) · [Переходы](raw/scale-transitions.txt)
