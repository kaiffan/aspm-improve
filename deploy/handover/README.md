# ASPM 1.0.1 Enterprise Delivery

Комплект кандидата содержит исходники, Helm Chart, конфигурации, deployment scripts, русскоязычные руководства и результаты квалификации. SBOM предыдущего образа сохранены для истории. Кандидат rc.11 требует нового сканирования пары release images.

Начните с [START_HERE](START_HERE.md), заполните [анкету инфраструктуры](checklists/INFRASTRUCTURE_INPUT.md) и примените [Standard HA](docs/04_DEPLOYMENT_GUIDE.md) в согласованном staging. Репетиция на одном узле описана в START_HERE. Состояние испытаний и решение по production находятся в [release gates](qualification/RELEASE_GATE.md).

| Для кого | Где начать |
|---|---|
| SRE / Kubernetes | [Установка](docs/04_DEPLOYMENT_GUIDE.md) · [Наблюдаемость](docs/13_MONITORING.md) · [Runbook](docs/16_TROUBLESHOOTING.md) |
| DBA | [PostgreSQL](docs/05_EXTERNAL_POSTGRESQL.md) · [Backup/Restore](docs/14_BACKUP_RESTORE.md) · [Upgrade/Rollback](docs/15_UPGRADE_ROLLBACK.md) |
| IAM | [Keycloak/AD](docs/06_KEYCLOAK_AD_SETUP.md) |
| SecOps / Expert / User | [Администрирование](docs/09_ADMIN_GUIDE.md) · [Пользователь](docs/10_USER_GUIDE.md) |
| Команда CI/CD | [API](docs/11_CICD_INTEGRATION.md) · [Примеры](integration-examples/README.md) |
| Владелец выпуска | [Паспорт](DELIVERY_MANIFEST.json) · [Сборка и перенос образов](docs/18_BUILD_AND_IMAGE_TRANSFER.md) · [Сообщение о передаче](HANDOVER_MESSAGE.md) |

Сверьте SHA256SUMS. Актуальные инструкции по S3 и DR находятся в Markdown. PDF в docs относится к предыдущей поставке. Лицензии upstream включены в исходники.
