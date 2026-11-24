# Версии GeneratedReport

POST `/api/aspm/v1/commits/{id}/reports/` с `{}` не требует finalize. При неоднозначности передаются `pipeline` либо `scan_ids`; optional expected_scanners задаёт coverage declaration. Старый `scan_set_id` работает как explicit legacy selection и не смешивается с новыми options.

Точка фиксации: чтение выбранных COMPLETED ScanRun rows, которые PostgreSQL уже запрещает менять. В короткой transaction под Commit lock создаются UUID ScanSet, FK-backed membership (0316), manifest с IDs/generations/artifact digests/metadata/selection policy, монотонная version и outbox. Worker не перечитывает live selection: HTML/JSON строятся исключительно по manifest. Поэтому upload/completion после фиксации не меняют содержимое версии.

Генерация потоковая, вне transaction регистрации. Проверенные COMPLETED reports и их bytes неизменяемы. Поздний scan обновляет live, а следующая версия создаётся только при новом запросе. Автоматической генерации после каждого scan нет. При отсутствии готовых results export возвращает 400; ожидание других scanners не нужно.

UNKNOWN coverage и неполные результаты не объявляются complete. Legacy reports, включая manifests с FAILED/PROCESSING, остаются читаемыми по прежним правилам.

Новый HTML различает UNKNOWN coverage и INCOMPLETE. Существующие bytes не регенерируются. [Real image HTTP](checks/image-http-smoke.json), [parallel report proof](checks/concurrency-green.json).
