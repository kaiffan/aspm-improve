# ASPM 1.0.1 RC2 — release hardening candidate

Preserves the RC1 OTP palette, Light/Dark/System, SVG branding and all Round1–5 performance work. Fixes applied-filter reset navigation, unstable/unbounded UI pagination, collection pagination in delete previews and late Select2 accessible labels. Adds behavioral regression tests and verified source/build metadata.

**Not Release Ready:** two inherited full-discovery import errors remain; no RC2 release alias or Stable promoted. See [report](RC2_REPORT.md), [tests](RC2_TEST_RESULTS.md), [controlled performance](RC2_PERFORMANCE.md), [Git/Docker provenance](RC2_GIT_PROVENANCE.md), [known issues](RC2_KNOWN_ISSUES.md) and [gates](RC2_RELEASE_CHECKLIST.md). No migrations, auth/API-contract changes or new integrations.

The RC1 notes below are historical.

# ASPM 1.0.1 Release Candidate 1

Корпоративный форк **DefectDojo OSS 3.5.100**, не независимая с нуля реализация. Product version **1.0.1**, channel **rc1**. Application source `5cdbc77fc9d4b8d0899069f5d44cd5241b2acae6`; image IDs и локальные теги — [release-images.json](measurements/release-images.json). Базовая performance-ветка `codex/performance-round5`, SHA021e751f3f95349698d502384c9df951fab331b6.

## Что включено

- Общий корпоративный UI: графитовая sidebar, компактные таблицы, формы/фильтры, карточки, dropdown/modal/pagination и оформление основных list/detail страниц Dashboard, Findings, Products, Engagements, Tests, Reports и Login.
- Light/Dark/System без миграции БД: выбор сохраняется, system учитывает OS, charts меняют оформление без изменения данных. Accessible focus/keyboard/mobile navigation; CSS/JS/fonts локальные.
- Собственный SVG-щит ASPM, mark/wordmark/favicon и заменяемая конфигурация. Акценты OTP lime/violet/orange; голубой фирменный цвет исключён. Семантическая раскраска severity остаётся различимой.
- Убраны Pro/PAYG menu, remote promotional/star banners, а также promotional session banners на error/long-request/import путях. Операционные/read-only предупреждения и лицензии сохранены. API error metadata `pro` оставлена для точной обратной совместимости; в нашем UI она не рекламируется.
- Версия ASPM/upstream/Git SHA показана в footer/support и standalone HTML report metadata/cover. LICENSE.md/NOTICE и сведения DefectDojo сохранены.
- Все Round1–5 сохранены: vulnerability prefetch, opt-in FAST OFFSET, Product batch IDs/count/none/detail, Test Jira prefetch, фильтрация Findings по Product и R5 Product/Dashboard aggregates. Бизнес-логика, API formats, permissions, deduplication и custom Engagements не переписывались.

## Проверка

189 Django tests passed, 8 skipped; 9 Node tests. Полная JSON/context совместимость на 104 парах R5/RC и дополнительный реальный rollback/restore с18 JSON-парами. Браузерные create/edit/login/denial прошли. Реальные ZAP import/reimport/duplicate peer завершили dedup; 40 дублей подтверждены. Подробности и ограничения — [TEST_RESULTS.md](TEST_RESULTS.md).

Свежий финальный mixed c25: Original13.253с/8.10RPS → RC5.013с/19.81RPS; R5 в той же серии4.904с/19.71RPS. Редизайну не приписывается ускорение накопленных ORM-патчей. 10 680 measured load requests без ошибок в завершённых сериях. Отдельные сценарии (filtered_product) быстрее исходного не стали; [PERFORMANCE.md](PERFORMANCE.md) показывает это явно. Новых P2 performance patches нет; [P2_AUDIT.md](P2_AUDIT.md).

Исходная БД по-прежнему **1 000 168 findings**, весь исходный миллион и168 fixtures сохранены. Write tests только на копии, теперь 1,000,293 rows: +40 первой инфраструктурной пробы, +84 успешного scan-цикла, +1 browser finding. Эти записи не удаляются и в основную БД не переносились.

## Статус выпуска

Демонстрационный RC: http://localhost:48086. Старая сборка8080 сохранена. App/nginx и worker1 работают на validation-копии; scheduler не запускается. Mail backend копии — locmem. Профилировочные middleware/binds убраны из demo.

Локальные образы `aspm:1.0.1-rc1` / `aspm-nginx:1.0.1-rc1`; stable1.0.1 и registry release не опубликованы. Для stable остаются унаследованный UI tie-order/pagination, настройка production secrets/hosts/TLS и отдельные HA/AMD64/capacity испытания. Полный список — [KNOWN_ISSUES.md](KNOWN_ISSUES.md). Сборка/запуск/откат: [BUILD](BUILD.md), [DEPLOY](DEPLOY.md), [ROLLBACK](ROLLBACK.md).
