# ASPM 1.0.1 RC2 — regression evidence

Источник runtime: `25fb63ae7b48b7eb87d39d0ee0f4c43d42d434fb`. Штатный `./run-unittest.sh --test-case unittests`, отдельный retained PostgreSQL/Valkey проекта `dd-final-tests`, internal offline network. Основная БД и validation-копия test runner не используются.

## Полный Django discovery

**8666 run; 8111 passed; 0 assertion failures; 2 import errors; 553 skipped.** [Машиночитаемые outcomes/skip reasons](rc2/raw/full-test-summary.json). Suite не зелёный; эти errors не скрыты и не превращены в skips.

Два blockers воспроизведены на frozen R5 и RC1:

- `unittests.test_ticket_comments` требует отсутствующий `dojo.notifications.ticket_comments`.
- `unittests.tools.test_trufflehog_parser` требует отсутствующий `unique_id_from_tool`.

[Version-origin evidence](rc2/raw/test-version-origin.json): теста ticket_comments в чистом3.5.100 нет; исходный TruffleHog test не требует нового helper. Внедрение будущей notification/dedup семантики выходит за запрет на функциональные изменения. Не добавлены stubs, новые skips или удаление тестов.

Наиболее частые существующие skips (все553 причины перечислены в JSON):

- 151: Skipping because V3_FEATURE_LOCATIONS is enabled.
- 133: Authorization is not configuration based
- 84: Authorization is not object based
- 20: This view does not inherit from <class 'rest_framework.mixins.DestroyModelMixin'>
- 18: This view does not inherit from <class 'dojo.api_v2.prefetch.mixins.PrefetchRetrieveMixin'>
- 18: This view does not inherit from <class 'dojo.api_v2.prefetch.mixins.PrefetchListMixin'>
- 17: Legacy authorization has no Reader/Writer/Maintainer/Owner distinction — the user is either in authorized_users (full member) or not (404). The RBAC role-gating semantics this test asserts don't apply post-Track-B.

## Новые guards и red/green

17 новых Django tests: 9 общей UI pagination, 6 Product filters/RBAC, 2 collection pagination. Дополнены существующие metadata checks. 3 новых Select2 cases; всего **12/12 Node tests passed**, 0 fail/skip. Строгий Ruff изменённых runtime/test файлов passed.

Эти же12 Node cases на frozen RC1 JS дают9 pass/3 fail: [red evidence](rc2/raw/javascript-red-summary.json). Новые guards действительно обнаруживают прежние ошибки.

- `inherited-errors-round5`: methods=2, passed=0, failure entries=0, error entries=2, skipped=0.
- `inherited-errors-rc1`: methods=2, passed=0, failure entries=0, error entries=2, skipped=0.
- `pagination-red-rc1`: methods=11, passed=6, failure entries=2, error entries=7, skipped=0.
- `grade-cache-red-rc1`: methods=45, passed=41, failure entries=2, error entries=0, skipped=2.
- `grade-cache-green-rc2`: methods=45, passed=43, failure entries=0, error entries=0, skipped=2.

В red baseline error/failure entries могут включать subtests; их нельзя складывать с числом методов. Полный suite выше содержит два отдельных loader errors.

Root cause grade test flakiness: debounce marker переживал database rollback и переиспользование Product PK между fixture cases. Очистка только соответствующего cache key в setup/cleanup теста устранила зависимость от порядка; **query assertions285/311/75/172 и production debounce не менялись**. Offline Jira DNS test принимает библиотечный NameResolutionError для `.invalid`; реальное соединение по-прежнему должно завершиться ошибкой.

## API / UI / import

- 208 сопоставимых пар: 152 полных JSON hashes (включая 12 ожидаемых403 denial pairs для users/notes без global permissions) и 56 HTML semantic comparisons. Ошибок сравнения: 0. Изменения только порядка ранее неупорядоченных UI ties отдельно перечислены и проверены по одинаковым первичным sort values; standard API order/data/bytes совпадают. Диагностический collector первоначально читал sort metadata после prefetch; исходная попытка и corrected recapture сохранены в `rc2/diagnostics/prefetch-order-metadata`. Это не изменение измеренных load samples.
- Standard/FAST pagination, Product count/none, filtering, sorting, permissions, vulnerability references, Dashboard/Simple Metrics и предыдущие R1–5 guards входят в полномасштабный discovery/profiles.
- Browser: 50 страниц/theme/viewport состояний, 12 функциональных checks; failures=0. Реальные Chromium143/Playwright1.57/axe4.14; screenshots в `rc2/screenshots`. Expanded dark filters: 2 desktop/mobile states, no axe/console violations. Light/Dark/System, sidebar keyboard, forms/dropdowns/navigation/selection проверены. [P0 before](rc2/raw/browser-p0-before.json) / [after](rc2/raw/browser-p0-after.json).
- Server pagination matrix: 140 проверок first/next/previous/last, missing/bad/negative/huge page, size50/invalid, filters/sort/empty, prefix Test page и admin/restricted; count, ranges, uniqueness, no adjacent overlap. [Matrix](rc2/raw/ui-matrix.json).
- Дополнительно6 desktop/mobile ×Light/Dark/System states и24 быстрых Next/Next/Prev/Prev перехода: фильтры, состав страниц и тема сохраняются; реальные generated Select2 controls обнаружены, JS errors0. [Rapid navigation](rc2/raw/browser-rapid.json).
- Browser CSRF create/edit, invalid/valid login, access-free denial: 5 checks. Дополнительные actual HTTP foreign-Product filter/FAST/ordering для access-free пользователя: count0. UI legacy denial status400 с403 body отдельно сохранён как inherited issue; API403/404 и отсутствие утечки подтверждены.
- Реальные ZAP import/reimport/duplicate peer: 3×201, deduplication_complete=true. Primary44 scanner findings, mitigated4, peer40, duplicates40; связанность и две actual vulnerability-reference rows в browser finding подтверждены. Флаг deduplication изменялся и восстановлен только на write-copy.
- Actual image rollback RC1↔RC2: 18 полных JSON pairs equal, worker остановлен на время переключения; очередь после=0, RC2 восстановлен.
- Django check, migration dry-run и OpenAPI --fail-on-warn passed; новых migrations нет. Финальные app/worker logs без ERROR/Traceback, OOM=false. Legacy Selenium suite не исполнялась: Selenium/chromedriver отсутствуют в test image; реальная браузерная проверка выше выполнялась через Playwright. Непроверенные acceptance400/10VU и external-node benchmarks не выдаются за выполненные.
