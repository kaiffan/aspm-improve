# ASPM HA Stabilization

Проверяемый application SHA `eee10e678c77480deceb794da92a1bc660cd0dee`. Helm `0.1.0-rc.8`, revision 12. Изолированный релиз `aspm` в `aspm-lab-orbstack`, один узел OrbStack, 2 web / 3 worker / 1 Beat. Production HOLD.

- [Вход через TLS](https://localhost:18736/login) · [HTTP лаборатории](http://127.0.0.1:18735/login)
- [Ресурсы, внешние зависимости и production gates](CORPORATE_HA_PROFILE.md)
- [Причина и разложение API acceptance latency](ACCEPTANCE_LATENCY.md)
- [Повторные rolling updates и непрерывность запросов](ROLLING_UPDATES.md)
- [Надёжность worker и восстановление outbox](WORKER_RELIABILITY.md)
- [Измеренные пики и бюджет PostgreSQL](POSTGRESQL_CONNECTION_BUDGET.md)
- [Интерфейс, screenshots и регрессия](UI_AND_REGRESSION.md)
- [Воспроизведение](REPRODUCE.md)
- [Пакет Helm](raw/aspm-0.1.0-rc.8.tgz) · [SHA-256 пакета](raw/chart-sha256.txt) · [Живые image IDs и StopSignal](raw/final-runtime.txt) · [Helm history](raw/helm-history.txt)

TLS URL использует сертификат именно этой лаборатории. Эти результаты относятся к синтетическому датасету. Квалификация отказов узлов и зависимостей, production ingress, ёмкость под целевой датасет, backup/RPO/RTO и подтверждённые корпоративные внешние параметры остаются условиями включения production.
