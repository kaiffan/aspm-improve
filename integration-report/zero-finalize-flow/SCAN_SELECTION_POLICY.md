# Политика выбора ScanRuns live-v1

1. Repository и Commit задаются авторизованным объектом; foreign IDs отвергаются.
2. Context: `pipeline:<pipeline_id>`, иначе `build:<build_id>`, иначе `legacy:<submitted_by_id>` для совместимости старых uploads.
3. При нескольких contexts автоматическое объединение запрещено. UI предлагает context; API reports требует `pipeline` или `scan_ids`, иначе 409. Независимые job_id одного scanner/scope/attempt также требуют явного выбора. Scanner Reports позволяет выбрать COMPLETED runs.
4. В context одна ячейка результатов — `(scanner_type, scan_scope)`. Последний успех выбирается по `attempt_number DESC`, `finished_at DESC NULLS LAST`, `created_at DESC`, UUID DESC. Job identity сохраняется в provenance; независимым scan scopes CI задаёт разные scan_scope.
5. Последний зарегистрированный статус выбирается отдельно по CI attempt, created_at, UUID. Более новый ACCEPTED/PROCESSING/FAILED не удаляет последний успех, но даёт INCOMPLETE. Все reruns доступны в истории; их findings не суммируются.
6. Explicit scan_ids: 1–1000 COMPLETED runs одного Commit/context, не более одного на scanner/scope. Смешанные pipelines, foreign или незавершённые IDs дают 400.
7. Без expected_scanners coverage UNKNOWN. Optional JSON array expected_scanners приходит в том же upload POST; пропуски дают INCOMPLETE. Противоречивые декларации дают INCOMPLETE. Legacy ScanSet предоставляет expected только при точном совпадении текущего состава.

Запросы возвращают не более 1001 scan slots и 101 context; UI показывает первые 100 contexts, прочие доступны через explicit IDs. Ни одного полного materialize observations.
