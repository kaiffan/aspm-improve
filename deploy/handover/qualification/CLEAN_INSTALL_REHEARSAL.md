# Репетиция чистой установки

Дата 26 ноября 2026. Выделенный OrbStack Kubernetes v1.36.5, ARM64, профиль local. Кандидат bef347c845ee, Helm 0.1.0-rc.9. Стенд создан специально для проверки. Подключены новая PostgreSQL 18.6, независимые broker/cache, новые Secrets и PVC. Шаги установки выполнены по START_HERE из распакованной копии с проверкой SHA256SUMS. Test fixtures и пары субъектов созданы отдельно через валидные API/управляющую команду.

```bash
shasum -a 256 -c SHA256SUMS
ASPM_LAB_PORT=18743 scripts/prepare-lab.sh orbstack aspm-lab-handover-rc local-path \
  postgres:18-alpine aspm-dual-lab/valkey:local \
  aspm-qualified/django:bef347c845ee-arm64 aspm-qualified/nginx:bef347c845ee-arm64
scripts/deploy.sh --context orbstack --namespace aspm-lab-handover-rc --release aspm \
  --profile local --arch arm64 -f values-aspm-lab-handover-rc.yaml --apply
kubectl --context orbstack -n aspm-lab-handover-rc port-forward --address 127.0.0.1 service/aspm-aspm 18743:80
scripts/smoke-test.sh --context orbstack --namespace aspm-lab-handover-rc --release aspm \
  --profile local --arch arm64 --url http://127.0.0.1:18743
```

На первой репетиции rc.8 исправлено quoting Go template для проверки ключей Kubernetes Secret. На превью rc.9 Chromium воспроизвёл overflow таблицы Finding location на 320–390 px. В финальной версии таблица прокручивается внутри собственного контейнера и имеет доступный label. Системный TLS bundle pip исправлен в образе. Первый smoke retry ClusterIP сохранён в исходных событиях, когда он появился. Preflight вывел PASS для SQL, PING broker/cache, fsync/rename и media.

Лабораторный профиль использует loopback HTTP, RWO и отдельные локальные зависимости. Для Keycloak, TLS и RWX production-подобные доказательства привязаны к своим SHA и окружениям. [Сводка](TEST_MATRIX.md) · [Release gates](RELEASE_GATE.md)

## Итог на финальном SHA

Helm revision 1 остановилась на миграциях после SIGKILL дочернего PostgreSQL backend. PostgreSQL автоматически вышел из recovery. Освободили ресурсы, остановив workloads собственного промежуточного стенда с сохранением его томов. На том же новом namespace повторили команду из архива. Helm revision 2 завершила миграции, Ready, schema/storage preflight, worker PONG и Helm test. От начала первого Helm install до успешного Helm test прошло около 6 минут 43 секунд, второй Helm этап и проверка заняли около 1 минуты 46 секунд. В финальном Helm test один ClusterIP запрос получил Connection refused, следующая попытка получила ожидаемый HTTP 200. Браузерный Login и все функциональные сценарии прошли.

Django check прошёл, makemigrations --check: No changes detected. Classic выполнил import/reimport и PATCH, DevSecOps принял шесть форматов и отдал два проверенных отчёта. Chromium прошёл 240 состояний и 11 проверок. PostgreSQL restore в пустую БД подтвердил 388 записей миграций, 3 Products, 6 ScanRuns и 1 Report. После восстановления private evidence повторно сверены шесть оригиналов и оба формата отчёта.

[Первый запуск](evidence/clean-initial-attempt.txt) · [PostgreSQL recovery](evidence/postgres-recovery.txt) · [Повтор](evidence/clean-install.txt) · [Live functional](evidence/live-functional.txt) · [Восстановление данных](evidence/restored-artifacts.txt)

## Upgrade и rollback

На отдельном синтетическом релизе выполнен переход eee10e678c77 / rc.8 → bef347c845ee / rc.9. Версии использовали одинаковые Django migration files. На целевой revision 2 миграции и 2/3/1 стали Ready. После failover прогона скрипт rollback принял письменный schema review и явное подтверждение цели. Revision 3 переключила приложение обратно на revision 1 (rc.8). Оба migrate --check и Helm test прошли. 12 исходных файлов и четыре файла отчётов сохранили общий SHA-256 после отката. Квалификация переходов с иной PostgreSQL schema остаётся отдельной задачей целевой площадки. Финальный Helm package получил переносимый README, манифесты всех профилей побайтово совпали с установленным пакетом.

[Upgrade](evidence/upgrade.txt) · [Rollback](evidence/rollback.txt) · [Сравнение Chart](evidence/portable-chart.txt)
