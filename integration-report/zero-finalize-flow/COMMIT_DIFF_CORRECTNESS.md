# Корректность Commit Diff

Сравнение читает только выбранные COMPLETED observations текущей generation. Finding identity сопоставляется в пределах scanner и scan_scope. Finding statuses не меняются.

FIXED подавляется при UNKNOWN/INCOMPLETE, отсутствующем scanner, ACCEPTED/PROCESSING/FAILED, неоднозначной выборке, разных pipeline contexts, разных scopes и пустом scan_scope. UI показывает UNKNOWN / NOT SCANNED / INCOMPLETE с предупреждением. Semgrep PROCESSING или отсутствие Trivy на target не создают ложный FIXED.

Политика разных pipeline IDs консервативна: отсутствие не доказывает исправление. Явно выбранные сопоставимые coverage declarations/scopes позволяют сравнение без finalize. Legacy сравнение направляется в тот же evidence view; чтение текущих mutable Finding для ASPM comparison исключено.

UI позволяет выбирать Base/Target GeneratedReport версии (`base_report` / `target_report`). Они читаются по frozen manifest, status и generations; foreign/незавершённая версия даёт 400. Поздний scan не меняет сравнение выбранных старых версий. Этот сценарий входит в финальный full suite.
