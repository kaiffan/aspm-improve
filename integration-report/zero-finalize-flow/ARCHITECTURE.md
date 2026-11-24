# Архитектура zero-finalize

Application SHA: `12dfcbe6bb0beb1cbe0bd411b2c26b820cb9d23a`. Base: `19cd7b4129de52e75eabaf0e07739e4c2b682f8e`, DefectDojo OSS 3.5.100 / RC5 integration. Ветка `feature/aspm-zero-finalize-flow`; исходные release branches не изменены.

Существующие API-only acceptance, immutable originals, transactional outbox, штатный importer/reimporter, generation publication и RC5 Finding write protocol сохранены. COMPLETED публикуется вместе с generation/count/severity в короткой транзакции. Автоматическая видимость реализована изменением чтения, без нового импорта или автоматического экспорта.

`dojo/aspm_ingestion/selection.py` задаёт bounded live selection. UI, canonical Commit page и reports используют эту policy. Overview складывает готовые ScanRun.severity_summary; Findings читает immutable FindingObservation выбранных COMPLETED generations, максимум 51 строку на страницу. CWE/CVE preview ограничен 20 observations. Чтение не создаёт ScanSet/GeneratedReport.

POST reports в Commit row lock выбирает COMPLETED rows и создаёт immutable ScanSet, membership, manifest, version и outbox. Celery генерирует HTML/JSON только из manifest после commit. Миграция 0316 и PostgreSQL guards сохранены.

Реальный concurrent test выявил существующую гонку Development environment: name не unique, два первых импорта создавали дубли, следующий get_or_create падал. Узкий fix в prepare_test сериализует только metadata creation через transaction advisory lock и детерминированно использует первую существующую запись. Уже завершённые ScanRuns/Tests/observations не переписываются. Parsing и Finding writes идут после завершения metadata transaction.

Функциональные gates пройдены. Полный performance release gate — HOLD из-за disk budget; [подробности](RELEASE_GATE.md).
