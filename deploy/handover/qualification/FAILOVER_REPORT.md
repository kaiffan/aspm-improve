# Отказоустойчивость

Предыдущая HA Stabilization, eee10e678c77, chart rc.8, revision 12. Один ARM64 узел, 2 web / 3 workers / 1 Beat, Traefik и shared PVC. Три последовательных restart под нагрузкой: TLS 0/3848 и прямой ClusterIP 0/4974 ошибок в финальных повторах без retries. Прогон через общий port-forward дал таймауты при параллельной передаче 48 MiB. С отдельным туннелем это взаимное влияние не повторилось. Обе реплики отдавали одинаковый SHA-256 оригинала. Отдельное удаление web pod на rc.7 — 0/1057.

Worker recovery при interrupt child 58,4 с, interrupt + замена pod 78,5 с, graceful scale-down 36,5 с. В каждом опыте завершились 3/3 скана и отчёт. Механизм сочетает late ack, session advisory lock и durable outbox с периодическим Beat.

Для enterprise подтвердите EndpointSlice/drain в целевом CNI, shared CSI, fencing при PostgreSQL failover, восстановление broker без дублей, IdP и webhook consumer unavailability. Потеря узла и HA зависимостей требуют multi-node стенда. [Статусы](RELEASE_GATE.md)

## Финальный bef347c845ee

В отдельном lab namespace предыдущий eee10e678c77 / chart rc.8 был обновлён до bef347c845ee / rc.9. Установилась топология 2 web / 3 workers / 1 Beat. Сопоставлены миграции, выполнен live Helm test. Четыре клиента без retries запрашивали Login с CSRF form и nginx CSS по ClusterIP 65 с на опыт. Уходящие Pods завершались до следующего опыта.

| Сценарий | Запросы | HTTP/TCP errors |
|---|---:|---:|
| Удаление одной web replica | 1 917 | 0 |
| Rolling restart 1 | 2 024 | 0 |
| Rolling restart 2 | 2 030 | 0 |
| Rolling restart 3 | 2 058 | 0 |

Текущие четыре опыта используют HTTP ClusterIP и публичные маршруты. Проверки активной сессии, Traefik TLS, worker interruption и сохранение хешей с двух web replicas относятся к описанному eee10e678c77. Проверки корпоративного ingress, отказов зависимостей как планового набора и отказов узлов остаются открыты.
[Сводные события](evidence/failover.txt) · [Replacement](evidence/pod-replacement.jsonl.gz) · [Rollout 1](evidence/rollout-1.jsonl.gz) · [Rollout 2](evidence/rollout-2.jsonl.gz) · [Rollout 3](evidence/rollout-3.jsonl.gz)
