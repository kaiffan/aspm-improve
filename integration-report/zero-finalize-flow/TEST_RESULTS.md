# Результаты тестов

## Django

| Build | Всего | Passed | Skipped | Failures / errors | Время |
|---|---:|---:|---:|---:|---:|
| Неизменённый integration 19cd7b4, свежий повтор | 8830 | 8277 | 553 | 0 / 0 | 413.594 s |
| Candidate 12dfcbe, финальная свежая БД | 8847 | 8294 | 553 | 0 / 0 | 413.260 s |

17 новых behavioral cases проверяют one-upload visibility, последовательные scanners, rerun selection, pending/failed history, immutable exports, selectors, coverage, comparison/versions, RBAC/polling/CSRF, pagination и duplicate environment metadata.

## JavaScript

17/17 passed: 12 существующих и 5 bounded polling tests. Проверены deadline через reload, максимум запросов, hidden page, auth error stop и revision reload.

## Strict API-only и safety

52/52 strict tests passed, 4.564 s. Expanded RC5 concurrency checks прошли в full suite; standalone 10 concurrency checks и реальные broker/SIGKILL recovery прошли. Сформированные report files совпадают с frozen membership/manifest; поздние runs не меняют bytes.

## Migration / schema / browser

Django check: 0 errors, один staticfiles.W004 warning в dev/test image из-за отсутствующего components/node_modules. Migration drift: No changes detected. Основная и ASPM OpenAPI schema прошли validate + fail-on-warn. Реальный browser smoke всех пяти вкладок и реальный HTTP/Celery flow прошли, включая повтор из immutable candidate image.

## Воспроизводители и preflight

Два исходных behavioral reproducer failed на 19cd7b4: reports требовал finalize, Findings суммировал reruns. Первый full запуск в production image получил missing vcr_unittest import errors; это неподходящий образ для полного test corpus. Далее reused keepdb показала восемь query-count assertions с тремя лишними ожидаемыми запросами. Fresh baseline 44 cases прошёл; fresh candidate 60 cases и затем full 8847 прошли. Importer code и expected query counts не менялись; финальное доказательство использует новую test_aspm_zero_releasegate DB.

При real concurrency дополнительно воспроизведён metadata race Development environment; fix и regression включены в финальный full suite.

## Performance

Новый малый A/B выполнен отдельно после functional suites. Он не заменяет frozen Core9 / mandatory acceptance на 1M. Этот полный performance gate не запускался из-за disk budget; [точные ограничения](PERFORMANCE_AB.md).

[Машинный итог](checks/test-results.json). Полные логи находятся в `logs/*.log.gz`.
