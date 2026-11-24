# Живые результаты коммита

Вкладки Overview, Scanner Reports, ASPM Report, Findings, Changes открываются непосредственно на canonical Project → Repository → Commit в API-only режиме; legacy evidence URL сохранён. ACCEPTED виден после commit регистрации и до импорта. PROCESSING не участвует в успешных counters. FAILED остаётся в пагинированной истории с безопасным error_code. Scanner Reports показывает ID, scanner, pipeline/job/CI attempt, время получения, status, findings_count и защищённый original download.

COMPLETED атомарно открывает immutable observations generation. Overview и ASPM Report показывают готовые severity counters и выбранные успешные ScanRuns. CWE/CVE доступны в Findings с cursor pagination по 50 строк. Мутируемые Finding не используются как источник исторической выдачи.

Polling: авторизованный state endpoint, только ScanRun/GeneratedReport aggregates, каждые 10 секунд, максимум 30 запросов / пять минут. Budget сохраняется через reload в sessionStorage. В скрытой вкладке запросы не отправляются; ошибка авторизации прекращает polling. После истечения budget обычное обновление страницы всегда читает актуальную БД. Миллион observations на polling не агрегируется.

Реальный browser smoke показал 8 selected findings, UNKNOWN coverage, четыре scanner types, Semgrep attempt 2, FAILED history и четыре downloadable JSON versions. В image HTTP smoke используется отдельный Commit 3. [Доказательство](checks/browser-smoke.json).
