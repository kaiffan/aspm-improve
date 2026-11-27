# Мониторинг

promtool проверил 39 alert и recording rules. Совпали версии JSON из чарта и handover. В Compose проверка публикации работала только с локальными сервисами.

Текущий результат live pipeline. Два private scrape targets UP. HTTP запросы увеличили счётчик, sample прочитан из Prometheus, VictoriaMetrics и Grafana datasource.. ASPMWebScrapeUnavailable подтвердил firing и resolve. После остановки VictoriaMetrics Prometheus зарегистрировал retry, затем VictoriaMetrics и Grafana вернули совпадающий счётчик. Корпоративные Prometheus, VictoriaMetrics, Alertmanager и exporter coverage остаются открыты. Ранее сохранённые результаты rc.10 доступны в deploy/handover/monitoring, отдельно от текущей квалификации.

При короткой остановке VictoriaMetrics наблюдались 3 180 повторно отправляемых samples. После восстановления Prometheus, VictoriaMetrics и Grafana вернули одинаковый HTTP counter 90. Общее число пропущенных samples в долговременном хранении не измерялось.
