# Изменённые файлы

| Файл | Назначение |
|---|---|
| `dojo/product/queries.py` | Общий scoped active-finding aggregate; для одного Product — constant group + Test-ID array, для нескольких — прежний batch GROUP BY |
| `dojo/product/api/views.py` | Использование helper; сохранение ordered ID list, точного count и пустого ответа |
| `dojo/query_utils.py` | Повторное использование существующего Test-ID array lookup |
| `dojo/finding/api/filters.py` | Импорт того же lookup, без изменения фильтра/прав |
| `dojo/home/views.py` | PK DISTINCT для трёх точных счётчиков; один local day/severity aggregate для всех графиков |
| `dojo/utils.py` | Опциональные готовые daily counts для punchcard; прежние вызовы работают без изменения |
| `unittests/test_round5_performance.py` | Полный ответ/порядок/empty/modes, scoped права и чужие findings, точные счётчики/дублирующие risk acceptances, chart oracle/timezones/boundaries |
| `perf-report/round5/` | Воспроизводимый harness, сырые HTTP/SQL/resource данные, планы, отчёты и графики |

Две оптимизации, три прикладных коммита: `26e232e2de` (исходный вариант), `ef29615d0c` (возврат прежних chart plans в промежуточной диагностике), `c6a6144ed9` (финальный единый дневной агрегат). Прикладной FINAL — `c6a6144ed93b83adb1fd4ea9daa2c5e417ecea37`; последующий коммит отчётов/дополнительной проверки visibility не меняет `dojo/`.

Нет миграций, новых индексов/сервисов/настроек, изменений шаблонов, custom Engagements/UI redesign, SSO, webhooks или дедупликации. Основной checkout с пользовательскими untracked notification-файлами сохранён. Предыдущие оптимизации и исходные отчёты находятся в истории Round4 и не представлены как новые исправления.
