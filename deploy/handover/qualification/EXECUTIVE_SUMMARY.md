# Итог квалификации ASPM 1.0.1

Application bef347c845eee8e16fdd6c3b5e8134eb499ece44 и Helm 0.1.0-rc.9. В исходном ARM64 стенде были Helm rc.8 revision 12 и application eee10e678c77. Источник прежней стабилизации — 6cc4408a3e. Фиксация конечного RC включает пересобранные Django и nginx, исправление TLS trust store pip и размещение Helm hooks на нужных узлах.

Окружение лаборатории — один Linux/ARM64 узел Kubernetes, отдельные DB, broker/cache и test PVC. Архитектура, настройки и ограничения описаны в [документации](../README.md). [Установка](CLEAN_INSTALL_REHEARSAL.md) · [Функциональные проверки](TEST_MATRIX.md) · [Совместимость](SCANNER_COMPATIBILITY.md) · [Security](SECURITY_REPORT.md) · [Нагрузка](PERFORMANCE_REPORT.md) · [Отказоустойчивость](FAILOVER_REPORT.md).

Production HOLD. Передача комплекта и выпуск в production — отдельные решения владельца. Проверьте [gate status](RELEASE_GATE.md).

Финальная автоматизация: Django 8 357 PASS, 553 inherited skips, 0 failures/errors. Strict API-only 86/86, JavaScript 17/17, Helm 20/20. Chromium 240 состояний и 11 действий, 0 ошибок. Шесть форматов успешно загрузились, повторились с теми же idempotency keys и проверили оригиналы и оба отчёта по SHA-256. OpenAPI v2, v3 и ASPM структурно совпали с установленной базой после исключения блока servers.

Из чистой PostgreSQL выполнена установка с восстановлением после SIGKILL backend во время первого migration Job. Успешное восстановление DB и private evidence проверено на отдельных целях. Web pod replacement прошла 0/1917, три rolling restart — 0/6112 HTTP/TCP ошибок на одном узле. Данные отказов узлов и зависимостей в corporate окружении остаются вне подтверждённого объёма.

Малый A/B/C на финальном SHA — 75 HTTP GET/с и 24/24 завершённых ScanRuns в каждом варианте. Client acceptance p50 32,54 / 23,12 / 37,61 ms. Нагрузка 1M остаётся NOT TESTED. Upgrade rc.8 → rc.9 и Helm rollback прошли, включая проверку fingerprint 16 файлов синтетических данных.
