# Инвентаризация Git и интеграция

| Позиция | Наблюдение |
|---|---|
| Origin | https://github.com/kaiffan/aspm-improve.git |
| Origin HEAD и исходная публичная линия | codex/performance-round4 · 716efb463387f82a0d13d5eae2541ac6b7dfee96 |
| Origin master | Ref отсутствовал при чтении GitHub. Исходного master SHA нет |
| Origin dev | На сервере отсутствует. Сохранённая локальная remote-tracking ссылка 71ba3f0e1b8f338384b5c25c396aa2db687909ae входит в кандидата |
| Исходный checkout | feature/ha-orm-scm-engagements-ui-webhooks · 207c7740bc. Имеет untracked delivery-каталоги, perf-report, release и два модуля notifications |
| Кандидат | release/aspm-1.0.1-final-qualification · исходный tip c6c275dc69feadd547d15be1b84e42ced14647d0 |
| Исходный application SHA | ff30da23b35adadb10b7813095c292bb0344ac26 |
| Финальный application SHA | c95177336f4d92580bf463e11d3d129490aba88c |
| Публикация | Владелец согласовал создание master после прохождения условий выпуска. Push не выполнялся |

Обновили GitHub refs без удаления локальных ссылок. Удалённый release/1.0.1-rc2 и обе performance-ветки входят в наследование кандидата. В исходном checkout есть пять уникальных коммитов старой линии. Их переносили в последующие ветки в составе RC5 и SCM, поэтому старую ветку отдельно не объединяли. У отдельных RC5-кандидатов оставили диагностические и альтернативные ветки. Два независимых локальных клона созданы с передачей объектов Git. В исходном checkout и соседних worktree изменений не вносили. Инвентарь содержал 30 записей worktree, из них 22 доступных, 8 отсутствующих и 3 с локальными изменениями на момент чтения. Stash отсутствовал.

| Модуль | Ветка или коммит | Реализовано | Проверка | В кандидате | Открыто |
|---|---|---|---|---|---|
| RC5 Finding и агрегаты | 3000b97550 | Да | PostgreSQL регрессия в FINAL_REGRESSION | Да | Полный прогон и производственный workload |
| Project, Repository, Commit, API-only | da9af68639, 0fa25bede5, 19cd7b4129 | Да | HTTP, порядок обработок, scope | Да | Все legacy API-матрицы |
| Zero-Finalize и отчёты | 12dfcbe6bb | Да | Celery, поздний scan, SHA-256 отчёта | Да | Массовая конкурентная генерация |
| Engagement policies | 0c988c25ac | Да | Целевые Django сценарии | Да | Корпоративные policies |
| Keycloak и RBAC | 0e0665f233 | Да | Модульные тесты, локальные роли | Да | Реальный корпоративный IdP и revocation |
| Classic и DevSecOps UI | ef24b34887, d6da4a7e24, bef347c845 | Да | Chromium, поиск, формы, фильтры, темы | Да | Остальные формы и браузеры |
| HA и external PostgreSQL | b77e295c22, 9131d8cac5 | Да | Helm, серверный dry run, отдельная локальная PostgreSQL | Да | Rollout в кластере без нехватки ресурсов |
| Outbound webhooks | ded0cf2417, b0106a2c63 | Да | Код и ранее зафиксированные проверки | Да | Текущая live доставка и replay |
| Monitoring, VictoriaMetrics, Grafana | 337ee35e9e, 77a6b79a2e | Да | Правила и JSON; текущий live-статус в MONITORING_QUALIFICATION | Да | Корпоративный monitoring |
| S3 и Storage recovery | ff30da23b3 | Да | MinIO TLS, versioning, multipart; Compose restore FS | Да | S3 recovery в отдельном namespace |
| Backpressure, Processing и Health | ff30da23b3, c95177336f4d | Да | HTTP, UI, сценарий сбоя конфигурации | Да | Soak и полный цикл Fault Injection |
| Handover и переносимость | eda4deeeca, 77a6b79a2e, 6eebcae0fa | Да | ARM64 build и loopback OCI round trip | Да | Полная квалификация на новом ПК и remote clone |

В диапазоне, ещё отсутствующем на удалённых ветках, самый большой Git blob — 25 465 688 байт, репозиторная scanner fixture. История содержит предыдущие сырые отчёты и диагностические файлы. Сканирование и ручная оценка артефактов перед публикацией остаются обязательными.
