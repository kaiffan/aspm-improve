# Бюджет PostgreSQL

Число web connection slots равно реплики × процессы × потоки. Celery child slots равны реплики × concurrency. К ним добавляются Beat, startup и readiness, migration Job и управленческие подключения. Оценки держат запас для overlapping rollout. Terminating pod могут дольше удерживать соединения.

| Профиль | Web slots | Celery child slots | Плановый резерв для приложения |
| --- | ---: | ---: | ---: |
| HA Standard | 8 | 6 | 25 |
| HA Standard при одном surge каждого компонента | 12 | 8 | 35 |
| High-throughput на максимуме HPA с surge | 16 | 10 | 45 |

HA использует CONN_MAX_AGE 60. Пример external overlay задаёт connect timeout 5 и verify-full. Advisory locks требуют direct или session pooled подключения. Keycloak, DBA, backup и мониторинг учитываются отдельно. Для реального PostgreSQL max_connections и resource profile согласовываются с владельцем базы.

[Измерения](SCALING_RESULTS.md) · [Внешний overlay](raw/profile-external-postgresql.yaml)
