# Failover на OrbStack

| Испытание | Действие и результат | Время | Статус |
| --- | --- | ---: | --- |
| nginx frontend и Django backend | Удалён один совместный web pod. 1 057 из 1 057 запросов завершились HTTP 200, включая Projects, Reports, API и статику. Аутентифицированная сессия сохранилась | 11 с до второй Ready реплики | PASS |
| Celery, прерывание активной задачи | SIGKILL одного дочернего процесса, подтвердившего обработку заранее выбранного синтетического ScanRun. Все три ScanRun завершились. Прерванный завершился со второй попытки. Повторы вернули те же IDs и по одному Finding на запуск | 60.1 с с сигнала до COMPLETED | PASS |
| Celery, замена pod | Один worker pod удалён с обычным grace period. Deployment восстановил 3 Ready | 45 с | PASS |
| Итоговый rolling update | RC7, 1 995 из 1 995 HTTP 200. Сессия оставалась действительной. Отдельный helm test прошёл со второй попытки | 137 с до завершения Helm upgrade | PASS |
| Shared storage | Два download URL вызваны через два web pod до и после замены. SHA-256 оригинала и JSON экспорта совпали | 11 с до второй Ready реплики | PASS |
| Параллельный workload | Classic import/reimport без Git, Finding PATCH, DevSecOps API upload, генерация отчёта, webhook retry/replay и UI reads. False Positive сохранён, Classic Test и Finding остались одной записью | См. индивидуальные логи | PASS |
| Масштабирование | 1 → 2 → 1 для web и 1 → 3 → 1 для worker. Очередь ingestion пуста перед очередным снижением масштаба. После эксперимента 2/3 восстановлены | См. переходы | PASS |
| Отказ узла | OrbStack имеет одну ноду | — | NOT TESTED |

Непрерывный workload при самом первом переходе с revision 7 на revision 8 зафиксировал 13 TCP connection refused из 1 728 запросов. У следующих двух измеренных rollout по ClusterIP таких ошибок не было. Helmsmoke использует отдельные подключения и сохранил краткий первоначальный отказ в логе. Проверки допускают локальную краткую потерю соединения при отдельных типах запуска клиента, которую следует исследовать перед выпуском.

[HTTP-трассы](raw/statistics.json) · [Поды](raw/web-deletion.txt) · [Worker recovery](raw/ingestion-recovery.json) · [Счётчики PostgreSQL](raw/worker-database-integrity.json) · [Worker replacement](raw/worker-pod-replacement.txt) · [Смешанный workload](raw/mixed-workload.json) · [Webhooks в том же прогоне](raw/mixed-webhook.json) · [Переключение профилей](raw/scale-transitions.txt)
