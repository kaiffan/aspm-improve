# Единый чеклист развёртывания

Площадка __________ · Context __________ · Namespace __________ · Release __________
ASPM owner __________ · SRE __________ · DBA __________ · IAM __________
Плановое окно __________ · Изменение / заявка __________

| Этап | Проверка | Время / evidence / ответственный |
|---|---|---|
| 1 | Сверены архив, SHA256SUMS, application/Helm provenance, нужная architecture | ____ |
| 2 | Заполнена [анкета](INFRASTRUCTURE_INPUT.md). Согласованы staging, security findings, доступы и rollback | ____ |
| 3 | Подготовлены registry, Secret references, DB/CA, broker/cache, PVC, ingress/TLS, Keycloak | ____ |
| 4 | Пройдён [pre-deployment](PRE_DEPLOYMENT.md). Preflight завершился с кодом 0 | ____ |
| 5 | Применён утверждённый Helm package и values. Записаны Helm revision, migration status и pod image IDs | ____ |
| 6 | Пройден [post-deployment](POST_DEPLOYMENT.md). Classic и DevSecOps проверены в синтетическом проекте | ____ |
| 7 | Проверены Keycloak/RBAC, monitoring, webhooks, backup/restore и schema rollback | ____ |
| 8 | [Release gates](../qualification/RELEASE_GATE.md) обновлены. [Приёмка](HANDOVER_ACCEPTANCE.md) подписана владельцами | ____ |

Зафиксируйте итоговое решение и ссылку на evidence __________
