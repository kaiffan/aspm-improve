# Импорт дашбордов

В Grafana откройте **Dashboards → New → Import**, загрузите нужный JSON из каталога [dashboards](../dashboards) и выберите существующий Prometheus-совместимый datasource VictoriaMetrics. UID дашбордов служат для переходов между панелями. Доступ к Security Posture ограничьте папкой и политикой datasource.

Для файлового provisioning подставьте UID существующего datasource в строковые значения `${DS_PROMETHEUS}` и удалите ключ `__inputs`. В ASPM Helm эту подстановку выполняет `monitoring.grafana.enabled` вместе с `monitoring.grafana.datasourceUID`. Используйте этот режим, только если корпоративный sidecar уже отслеживает ConfigMap соответствующего namespace и label. По умолчанию Helm не создаёт Grafana ресурсы. Источник Grafana использует query endpoint VictoriaMetrics. Подключение write endpoint настраивается только в Prometheus.
