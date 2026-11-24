# Совместимость API

Сохранены POST scans, GET scan UUID, GET commit scans, POST/GET commit reports, protected original/report downloads и необязательный finalize. Первый upload возвращает 202 + ScanRun ID; replay по прежнему возвращает 200 + тот же ID. Разное содержимое/metadata с одним ключом даёт 409.

Reports с `{}` теперь внутренне фиксирует live selection, а не требует ранее созданный finalize. Explicit `scan_set_id` сохраняет legacy semantics, foreign/несуществующий ID отвергается. При нескольких contexts или независимых jobs требуется безопасный выбор.

Новые optional поля: upload expected_scanners; report pipeline/scan_ids/expected_scanners. Finalize отмечен deprecated, остаётся scoped machine operation. CI examples выполняют только upload; status опционален. Legacy helper filename finalize.py сохранён, но helper вызывает reports напрямую.

OpenAPI, README, GitHub Actions, GitLab CI и curl helper обновляются вместе с кодом. API session не получает submit/retry/report machine scopes. Отдельная browser export operation требует Product edit и CSRF; она не принимает scans.
