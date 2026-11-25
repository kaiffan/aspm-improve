# Историческая корректность и lost updates

Финальный B прошёл RC5 oracles для 5, 10 и 25 конкурентных PATCH, PATCH одновременно с чтением, reimport со stale instance и независимым PATCH, async dedup с PATCH и реального import/dedup. Оракулы сверяют итоговые значения полей после реальных конкурентных операций. Доказательство относится к проверенным сценариям.

Проверки Zero-Finalize включают неизменность оригиналов, observations, pinned versions, immutable membership, поздние запуски, отсутствие ложного FIXED и неоднозначные pipelines. Реальный overlap сохранил JSON/HTML SHA-256 после позднего scan. Recovery сохранил Test и ровно 3 000 observations после SIGKILL.

Read-only fingerprint защищённого seed совпал. Rows 1 000 000, sum_ids 500 000 500 000, xor -6518521627913831325, SHA-256 c0ad4fd6acaba524626725d05dcf8bc9bd771fc8a6002ce1065845a0856eb87c. Малая PostgreSQL rehearsal восстановила 600 Findings, 600 observations, шесть ScanRuns и три GeneratedReports с совпадающими fingerprints. Native 1M snapshot и restore proof ожидают VM.

[Тесты](raw/regressions.json) · [1M fingerprint](raw/protected-fingerprint.json) · [Dump/restore](raw/local-restore.json)
