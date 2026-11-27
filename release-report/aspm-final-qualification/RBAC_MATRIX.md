# Матрица RBAC

| Роль или principal | Сценарий | Наблюдение |
|---|---|---|
| SecOps локальный | Login, Classic, DevSecOps, Health, создание Product Type | Проверено Chromium |
| Reader с одним Product | Список Projects и direct Health | Выданный проект виден, второй скрыт, Health 403 |
| Reader с двумя Product | Список Projects и direct Health | Два проекта и Health 403 |
| Reader без Product | Пустой список Projects и direct Health | Empty state и Health 403 |
| CI token | Собственный original artifact и cross-Product запрос | 200 на собственный, 404 на чужой |
| Expert и управляемые Keycloak роли | Protocol и grants | Целевой Django; текущий живой браузерный цикл не выполнен |
| Истёкшая сессия | Удаление локальной cookie | Перенаправление на login |
| Отзыв SSO-группы | Живой IdP и TTL | NOT TESTED |

Доступ к webhook configuration, UI admin и полный набор legacy API RBAC для всех ролей остаются открыты. [Действия Chromium](UI_INTERACTION_COVERAGE.md).
