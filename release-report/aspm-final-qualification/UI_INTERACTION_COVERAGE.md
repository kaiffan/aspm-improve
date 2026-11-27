# Интерактивные сценарии

Chromium 158.0.8127.88, 147 зарегистрированных переходов, 140 PASS, 0 FAIL, 16 снимков. Действия ниже выполнены мышью или клавиатурой с проверкой итогового содержимого и переходов. Результаты responsive-переходов включены в метрики прогона и вынесены в [таблицу](RESPONSIVE_TESTS.md).

- PASS · SecOps local browser login
- PASS · Projects search returns matching product and empty results
- PASS · Classic Product Type create and persisted form values
- PASS · Workspace Reports tabs and search
- PASS · SecOps loads dashboard
- PASS · SecOps loads classic
- PASS · SecOps loads projects
- PASS · SecOps loads findings
- PASS · SecOps loads reports
- PASS · SecOps loads processing
- PASS · SecOps loads health
- PASS · SecOps loads repositories
- PASS · Findings filter opens via keyboard
- PASS · Mobile nav opens and Escape restores focus
- PASS · axe-core projects
- PASS · axe-core processing
- PASS · axe-core reports
- PASS · axe-core findings
- PASS · axe-core health
- PASS · reader-one project scopes and protected System Health
- PASS · reader-two project scopes and protected System Health
- PASS · reader-none project scopes and protected System Health
- PASS · Invalidated local session returns to login
- PASS · Classic Product description edit and persistence
- PASS · Classic native Product report opens from configured route

Базовый повторный smoke входа, списка проектов, переключения вкладки Reports и responsive проверки 390/1440 также прошёл на Firefox 144.0.2 PASS, WebKit 26.0 PASS. Отдельные сценарии с истечением TTL Keycloak, отзывом SSO-группы, Expert, повторной отправкой формы, массовым triage и всеми действиями настройки интеграций в текущем живом Chromium-прогоне остаются NOT TESTED. Очистка cookie проверяет потерю локальной сессии.
