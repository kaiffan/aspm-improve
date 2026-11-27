# Репетиция установки

Созданы независимые локальные клоны через git clone --no-local, без workspace artifacts и без старого worktree в build context. На c95177336f4d92580bf463e11d3d129490aba88c проверен путь git archive → build-images.sh. Собраны оба ARM64 образа; nginx сгенерировал статику. Оба образа опубликованы в отдельный loopback OCI registry, загружены обратно по digest, проверены platform, OCI revision и ID. Пройден Compose preflight и начаты HTTP smoke. В исходной чистой установке выполнены миграции PostgreSQL.

Локальный Helm live smoke на исходной квалификации подтвердил Ready для 1 web, 1 worker и 1 Beat после ограничения тестовых requests. HTTP smoke прошёл. Нагрузочная HA-проверка остаётся открытой. Сохранены резервный синтетический dataset и снимки QA.

На ревизии с исправлениями `e2f3f244f478` повторили сборку и loopback push/pull по digest для Debian Django и nginx. В отдельном Compose-проекте прошли миграции с пустой PostgreSQL, проверка схемы и private storage preflight. Запустились web, worker, Beat, nginx и Valkey. `/login` ответил HTTP 200. Сценарий API на синтетических данных прошёл для 6 форматов и двух версий отчёта. Скрипт публикации подтвердил digest и revision обоих образов и сформировал values для Helm. [Проверка GitHub](MASTER_PUSH_VERIFICATION.md)
