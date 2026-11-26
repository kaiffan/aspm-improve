# 01 | Продукт и рабочие пространства

ASPM 1.0.1 использует DefectDojo OSS 3.5.100 как основу. Classic хранит обычные продукты и результаты сканеров. DevSecOps добавляет отправку из CI, историю по коммитам и отчёты о покрытии.

| Задача | Куда идти |
|---|---|
| Управлять уязвимостями и legacy-интеграциями | Classic → Product Type → Product → Engagement → Test → Finding |
| Проследить сканирование сборки | DevSecOps → Project → Repository → Commit → ScanRun |
| Понять неполное покрытие | Commit → pipeline → статусы и ожидаемые сканеры |
| Сравнить коммиты | Repository → Commits → Compare. Выберите одинаковый scan scope и набор сканеров |
| Выгрузить данные | Classic Native HTML Report или DevSecOps HTML/JSON с версиями |

Project соответствует Product в модели доступа. Classic Engagement может существовать без Repository или Commit. При активном API-only результаты сканера поступают через REST API. Действия зависят от роли, scope токена и разрешений проекта.

[Архитектура](02_ARCHITECTURE.md) · [Администрирование](09_ADMIN_GUIDE.md) · [Руководство пользователя](10_USER_GUIDE.md) · [CI/CD](11_CICD_INTEGRATION.md)
