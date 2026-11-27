# Параметры от владельца

| Владелец | Поле | Значение |
|---|---|---|
| SRE | Existing Prometheus или согласованный dedicated | ____ |
| SRE | Версия Prometheus/Operator, namespace и selector labels | ____ |
| SRE | Разрешённый scrape network, TLS/SAN и частота | ____ |
| SRE | Имена cluster, environment, namespace, release | ____ |
| VictoriaMetrics | Single, cluster/vminsert либо proxy/vmauth | ____ |
| VictoriaMetrics | Полный HTTPS remote_write URL и tenant, если применимо | ____ |
| VictoriaMetrics | Basic, bearer либо mTLS и имя соответствующего Secret | ____ |
| VictoriaMetrics | Имя CA Secret, source network, retention и HA dedup policy | ____ |
| DBA | Существующий exporter либо отдельная роль и Secret, доступ к pg_stat_statements | ____ |
| Platform | KSM, cAdvisor, CSI, Traefik и node exporter в пределах ASPM | ____ |
| SecOps | Разрешение на агрегаты Security Posture и доступ к ним | ____ |
| On-call | Один rule evaluator, Alertmanager URL, команда, каналы, severity policy | ____ |
| On-call | Runbook base URL и согласованные SLO/пороги | ____ |

Grafana использует уже настроенный источник VictoriaMetrics. JSON импортируются на стороне владельца. Значения секретов передавайте средствами Kubernetes Secrets или корпоративного vault.
