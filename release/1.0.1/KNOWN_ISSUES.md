> RC2: см. [RC2_KNOWN_ISSUES.md](RC2_KNOWN_ISSUES.md). Ниже сохранён исторический отчёт RC1; его цифры/открытые дефекты не подменяют новую проверку.

# Ограничения RC

- Локальный кандидат на ARM64/16 GiB не доказывает production capacity 10–20 млн findings или преимущество над сторонними ASPM. Отдельные 16 vCPU/32 GiB app и HA PostgreSQL ещё не испытывались.
- Full Product API сохраняет все IDs в исходном порядке. Размер, Python-память и сериализация растут с числом findings. Для собственных клиентов доступны opt-in findings=count/none; полный ответ ими не подменялся в сравнении.
- Точные COUNT, широкий DISTINCT и большой OFFSET остаются дорогими. FAST OFFSET экспериментальный и opt-in. Findings/Test UI по-прежнему могут занимать секунды на локальном миллионе. P2-аудит подтвердил дорогую выборку страницы по severity и DISTINCT title для фильтра, а не доминирование COUNT. Нового P2-патча нет; причины и планы в P2_AUDIT.md.
- Синтетический миллион не моделирует production-плотность endpoints, notes, vulnerability IDs и дедупликации. Smoke import/reimport проверяет механизм, а не массовые scanner integrations.
- Визуальная проверка выполнена в Chromium, не является cross-browser/screen-reader сертификацией. Нужны ручные acceptance-тесты целевых браузеров и пользователей.
- TLS, корпоративная auth/integrations, backup restore, HA/failover, registry signing/SBOM/scanning и AMD64 deployment не сертифицированы этим локальным запуском. Стабильный 1.0.1 tag не публикуется.
- Старый API-only gateway Round 5 на 48085 не обслуживал static. Для browser baseline создан отдельный корректный gateway. Его пустые стили не используются как показатель улучшения RC.
- Первая нагрузочная серия пересеклась со сном macOS и была остановлена guard. Её сырые результаты сохранены в raw/interrupted-window и исключены из итоговых процентов. Увеличен только timeout диагностической команды Docker; серверные параметры и пороги памяти не менялись.

- В локальном private runtime Django check сообщает о стандартных ключах/`ALLOWED_HOSTS=*`. Они унаследованы от perf-стенда и не являются production-конфигурацией. Привязка gateway к loopback сохранена. Для production требуются реальные secret/hosts/TLS; существующий credential encryption key нельзя менять без миграции сохранённых credentials.
- Подтверждено пересечение соседних UI-страниц при default `numerical_severity` и равных severity: 1 ID на проверенной паре страниц как в замороженном Round 5, так и в RC. Это унаследованное отсутствие tie-breaker, не изменение UI-кода; [измерение](measurements/inherited-pagination.json). Порядок молча не менялся. Browser navigation smoke с явным title-order на уникальных fixture titles проходит; это не гарантирует уникальность title в production. Для стабильного выпуска нужна отдельная проверенная политика tie-breaker.

- В новом финальном closed-loop c25 сценарий filtered_product имеет p95 хуже Original в обеих R5 и RC, несмотря на общий throughput ×2.45. Не заявляется ускорение всех маршрутов; это требует отдельного offered-load/SQL эксперимента. Полные числа в PERFORMANCE.md.
- Унаследованный UI denial handler возвращает400 с403 body; API корректно ограничивает данные (403/404 detail,0 list). Статус UI не менялся ради косметического RC.
