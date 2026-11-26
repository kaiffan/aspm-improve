# ASPM 1.0.1 | Release candidate

Application bef347c845eee8e16fdd6c3b5e8134eb499ece44 на основе DefectDojo OSS 3.5.100. Chart 0.1.0-rc.9 из b5c7161ed848a7015dca87da43a52bf5f9bc69d7. Placement-манифесты зафиксированы в 9131d8cac5. Историческая HA Stabilization относится к eee10e678c77, Helm rc.8, evidence 6cc4408a3e.

- Django build обновляет vendored certifi в pip до bundle из pip 26.2.2 и проверяет три CA store на исключение недоверенной emSign root. Celery использует тот же образ.
- Chart передаёт nodeSelector, affinity и tolerations в migration и test hooks. Их размещение следует требованиям архитектуры и выделенного пула узлов.
- Finding detail на узких экранах прокручивает таблицы локально с доступом через клавиатуру. В интерфейсе указан канал enterprise-rc.
- Комплект включает русские инструкции, overlays, Bash/Python deployment pipeline, CI/CD примеры, чеклисты и квалификацию.

Кандидат сохраняет Classic и DevSecOps workflows. Дельта относительно eee10e678c77 по схеме отсутствует. Для обновления с других версий обязателен отдельный schema review. [Результаты](qualification/TEST_MATRIX.md) · [Security](qualification/SECURITY_REPORT.md)
