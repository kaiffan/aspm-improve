# План воспроизведения нагрузки

Сохранённые маршруты и веса в core9-plan.json. Для A и B выполните c1/c5/c10 по одному и c15/c25 по три раза, после одинаковой подготовки снимка и одинаковой настройки PostgreSQL/CSI/Ingress. Сохраняйте фактическую интенсивность, HTTP, shape, business outcomes и все попытки. Для обычной сборки применяйте small_workload.py. Диагностический acceptance_probe.py использует Server-Timing middleware из исходного пакета и отдельный тестовый токен. Схема входа в скрипте.

Для 1M подготовьте согласованные native Linux/AMD64, PostgreSQL, storage и снимок. Восстанавливайте общий снимок перед каждым из трёх 10-VU Acceptance повторов на вариант. Mixed workload для 15–25 активных пользователей требует независимых identity, sessions и тестовых проектов. Фиксируйте пропорцию read/write/report, ошибки без retry, PostgreSQL connections/locks/WAL/I/O и проверку фактических записей.

| Операция Acceptance | p90 |
|---|---:|
| Import 400 Findings E2E | ≤110 s |
| Finding Browser Open | ≤60 s |
| Finding POST | ≤5 s |
| Native HTML Report E2E | ≤70 s |

[Методика и статус](../PERFORMANCE_REPORT.md). Полный 1M runner зависит от утверждённых A/B образов и согласованного снимка.

## Версионированный драйвер

Каталог native содержит Core9, Acceptance, workload lock и искусственные XML fixtures. Для повторения исходного A/B передайте оператору локальный Git репозиторий с двумя сохранёнными точными baseline SHA из native/build.py. Для сравнения с текущим кандидатом сначала утвердите B, согласуйте общий runtime package set, зафиксируйте SHA и используйте новый state directory. Смена кандидата требует обновить expected A/B identity и проверить сопоставимость; она не меняет workload-lock.

```bash
python3 native/build.py --repo "$ASPM_BENCH_REPO" --state "$ASPM_BENCH_STATE" --plan
python3 native/campaign.py --state "$ASPM_BENCH_STATE" plan
npm ci
npx playwright install chromium
export NODE_PATH="$PWD/node_modules"
python3 native/build.py --repo "$ASPM_BENCH_REPO" --state "$ASPM_BENCH_STATE"
python3 native/campaign.py --state "$ASPM_BENCH_STATE" init
python3 native/campaign.py --state "$ASPM_BENCH_STATE" seed
python3 native/campaign.py --state "$ASPM_BENCH_STATE" core9
python3 native/campaign.py --state "$ASPM_BENCH_STATE" acceptance
python3 native/summarize.py --state "$ASPM_BENCH_STATE"
python3 native/campaign.py --state "$ASPM_BENCH_STATE" stop
```

Оставьте guard checks включёнными. Native runner сам создаёт отдельную DB и volume labels. Проверьте содержимое raw перед передачей. Внутренние credentials state, dump и рабочие PVC остаются у владельца тестовой площадки.

Для small-data повтора используйте small_workload.py с доверенным application image и Python requests. Запускайте в собственном test Pod с маршрутом к Service aspm-aspm. На stdin передайте одну JSON запись с короткоживущими полями admin, password, project, repository и ingestion для синтетического проекта. Скрипт записывает статусы, latency, accepted scans, actual completion и внутренние timings. Передайте stdout без stdin. Лимиты и профили трёх прогонов описаны в отчёте.
