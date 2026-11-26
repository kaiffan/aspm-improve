# Роли и рабочие области

| Роль | Основная навигация | Проверка |
| --- | --- | --- |
| User | Мои проекты, Classic, Reports, профиль | Портфели из одного, двух и нуля проектов. Findings и настройки возвращают 403 |
| Expert | Security overview, Projects, Classic, Findings, Reports и сравнение | Findings 200, Settings 403. Строгие тесты проверяют разрешённый False Positive и запрещённую подмену названия |
| SecOps | Обе рабочие области, Findings, Reports, Integrations, Webhooks, Access Management, Health и Settings | Findings и Settings 200. Действия используют существующие backend permissions |

Синтетический TLS-стенд проверяет callback Keycloak для того же исходного кода. В OrbStack сохранение сессии проверяется на отдельном локальном входе через общую PostgreSQL.

[Матрица](raw/browser-after.json) · [Регрессии](REGRESSION_RESULTS.md)

В Keycloak проверено живое снятие синтетического гранта. Новый вход сразу потерял доступ, текущая сессия получила 403 через 118.55 с при TTL 120 с. Исходная тестовая привязка восстановлена. [Отзыв гранта](raw/keycloak-revocation.json)
