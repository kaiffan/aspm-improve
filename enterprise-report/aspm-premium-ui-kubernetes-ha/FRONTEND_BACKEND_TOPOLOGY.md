# Совместные nginx и Django pod

В каждой из двух serving replicas nginx обслуживает статику образа и проксирует HTTP в локальный uWSGI socket. Совместный pod связывает rollout nginx и Django, даёт один Service и исключает отдельный сетевой hop между ними. Соседняя реплика независимо готова обслуживать тот же запрос.

Доступность nginx проверяется выдачей настоящего CSS. Django startup/readiness/liveness используют внутренний health port. При graceful drain nginx получает SIGQUIT после паузы для удаления endpoint. Django остаётся внутри pod и даёт nginx завершить активные запросы. Фактическая доступность измерена при rollout и замене pod.

[Результаты](FAILOVER_TEST_RESULTS.md) · [Политика](POD_DISRUPTION_POLICY.md)
