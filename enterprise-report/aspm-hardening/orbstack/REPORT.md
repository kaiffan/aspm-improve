# ASPM в OrbStack Kubernetes

**Установка остаётся заблокирована на планировании pod.** Контекст `orbstack` отвечает. В namespace `aspm-lab-orbstack` созданы отдельные Secret, PostgreSQL, Valkey broker, Valkey cache и три PVC. Scheduler оставил pod в `Pending` из-за `node.kubernetes.io/disk-pressure:NoSchedule`. PVC используют `WaitForFirstConsumer`, поэтому тоже остались `Pending`. Helm release не создан. [Журнал попытки](install.log.gz) · [События scheduler](scheduler-events.txt) · [Pod и PVC](kube-pending.txt)

| Проверка | Результат |
|---|---|
| OrbStack | Kubernetes 1.36.5, один узел ARM64 |
| nodefs и imagefs после очистки | 12,85 ГиБ свободно из 213,25 ГиБ. Для снятия DiskPressure требуется 31,99 ГиБ |
| Helm `0.1.0-rc.2` | 12 chart-тестов. 49 ресурсов прошли проверку Kubernetes schema в пяти конфигурациях |
| OrbStack API server | 10 объектов Helm, включая миграционный Job и HTTP test Pod, приняты в server dry-run |
| Реальный Helm install, `helm test`, upgrade, rollout и in-cluster webhook delivery | NOT TESTED из-за DiskPressure |
| Webhook Django/TLS, локальный Docker | 37/37 PASS |

После первой очистки на узле было 6,71 ГиБ свободного места. По согласованию удалены два остановленных контейнера и два локальных тома завершённого синтетического бенчмарка `aspm-api-ingestion`. В Docker они занимали 6,75 ГБ. Результаты и рецепт воспроизведения сохранены в ветке `codex/aspm-api-only-ingestion`, в `docs/aspm-api/validation.md`. Основная PostgreSQL, база ASPM Acceptance и активный Compose-стенд сохранены. [Замер после очистки](disk-after-cleanup.json)

Эффективный конфиг kubelet задаёт 5% для срабатывания и ещё 10 процентных пунктов `evictionMinimumReclaim` для восстановления. До порога восстановления не хватает 19,14 ГиБ. После достижения порога kubelet выдерживает пять минут перед снятием `DiskPressure`. При `DiskPressure=False` проверьте локальные теги PostgreSQL и Valkey из `dependencies.yaml`, которые kubelet может удалить при сборке мусора, и выполните `deploy/labs/orbstack/install.sh --resume`. Этот запуск повторно использует уже созданные Secret и PVC. [Политика восстановления Kubernetes](https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/#minimum-eviction-reclaim)

## Что исправлено в Helm

В пакете `0.1.0-rc.1` правило `.helmignore` `tests/` исключало `templates/tests/http.yaml`. Пакет `0.1.0-rc.2` исключает только корневой каталог с тестами разработчика. Новый regression-тест создаёт `.tgz`, рендерит его с обоими значениями `tests.enabled` и проверяет, что opt-in действительно добавляет Pod с `helm.sh/hook: test`. Артефакт и SHA-256 находятся рядом с этим отчётом. [Сборка и проверки](helm-validation.txt) · [Проверка API server](kube-apiserver-validation.txt)

## Вебхуки

Целевой набор Django прошёл 37/37. Он проверяет transactional outbox, идемпотентность, конкурентные изменения Findings, фильтры, ошибки и повторы, replay, ротацию, RBAC и CSRF. Для положительного случая отдельный тест устанавливает настоящее TLS-соединение с локальным получателем и проверяет HMAC над полученными байтами. Тестовый resolver нужен только внутри этого теста. Политика работающего приложения сохранена. [Журнал Django и TLS](webhook-django-final.log.gz) · [Возможности вебхуков](WEBHOOK_CAPABILITIES.md)

Сквозной прогон прошёл на изолированном ARM64 стенде Docker с реальными HTTP, PostgreSQL, Celery worker и beat. Время полного сценария составило 178,87 с и включает ожидание тиков dispatcher. Это время сценария, а не latency внешнего получателя. `scan.completed` сформировался после обработки реального API-only скана. Подписка `High` получила событие, подписка `Critical` осталась без доставок. На зарезервированном `.invalid` произошла ожидаемая DNS-ошибка. После двух попыток доставка стала `DEAD`. Replay сохранил ID доставки и историю, после двух новых попыток в истории стало четыре. Дополнительно проверены доступ администратора, HTTP 403 для viewer, отклонение loopback endpoint, одноразовый показ и ротация секрета, тестовое событие, отключение и архивирование. [HTTP smoke evidence](webhook-http.json)

[Снимок истории доставок](webhook-delivery-history.png): две попытки `webhook.test` и четыре попытки `scan.completed` после replay.
