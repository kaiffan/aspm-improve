# Репетиция установки

Созданы независимые локальные клоны через git clone --no-local, без workspace artifacts и без старого worktree в build context. На c95177336f4d92580bf463e11d3d129490aba88c проверен путь git archive → build-images.sh. Собраны оба ARM64 образа; nginx сгенерировал статику. Оба образа опубликованы в отдельный loopback OCI registry, загружены обратно по digest, проверены platform, OCI revision и ID. Пройден Compose preflight и начаты HTTP smoke. В исходной чистой установке выполнены миграции PostgreSQL.

Финальный локальный Helm live smoke подтверждён после ограничения тестовых requests. 1 web, 1 worker и 1 Beat достигли Ready. Helm HTTP smoke завершился. Нагрузочный HA gate открыт. Сохранены резервный синтетический dataset и снимки QA. GitHub clean clone итогового master отсутствует до завершения release gate.
