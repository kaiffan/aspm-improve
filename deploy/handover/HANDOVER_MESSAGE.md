# Сообщение получателю

Передаю кандидат ASPM 1.0.1. В архиве находятся исходники, Helm Chart, профили, шаблоны Secret references, скрипты, инструкции и результаты испытаний. Сверьте SHA256SUMS и откройте [START_HERE](START_HERE.md).

Для staging подготовьте контекст Kubernetes, namespace, архитектуру, registry, внешний PostgreSQL и CA, broker/cache, два RWX PVC, DNS/TLS и Keycloak. Заполните [анкету](checklists/INFRASTRUCTURE_INPUT.md), затем примените [руководство установки](docs/04_DEPLOYMENT_GUIDE.md) и values из config. Для пользователей и CI/CD доступны [руководства](README.md).

Сохраните действующие БД, volumes, PVC и данные прежних лабораторий. Upgrade/rollback согласуйте с DBA по схеме и backup. Production требует отдельного решения владельца. Оставшиеся проверки перечислены в [release gates](qualification/RELEASE_GATE.md).
