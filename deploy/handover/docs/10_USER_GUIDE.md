# 10 | Руководство пользователя

1. Откройте доверенный URL и войдите через Keycloak. DevSecOps → Projects показывает доступные проекты. В Classic те же права определяют видимость Product Type и Product.
2. Откройте Project → Repository → Commit. Сверьте полный SHA, pipeline и scan scope. В Scanner Results проверьте версию и статус. ACCEPTED — регистрация, PROCESSING — обработка, COMPLETED — опубликовано, FAILED — анализ владельцем CI.
3. Откройте Reports. Для Classic выберите Engagement и Native HTML Report. Для DevSecOps выберите Commit, pipeline и версию HTML/JSON. Сверьте ожидаемые сканеры. По pending, failed или missing свяжитесь с владельцем pipeline.
4. Для отсутствующего проекта сообщите владельцу название, свой корпоративный ID и нужный доступ. После назначения группы повторите вход или дождитесь согласованного refresh.
5. Для клавиатуры используйте Tab и Enter. Темы Light/Dark/System доступны в меню. Длинные таблицы прокручиваются в собственной области.

![Classic на синтетических данных](../screenshots/classic.png)

![Commit на синтетических данных](../screenshots/commit.png)

![Карточка Finding на 320 px. Выделена область прокрутки файла](../screenshots/finding-320.png)
