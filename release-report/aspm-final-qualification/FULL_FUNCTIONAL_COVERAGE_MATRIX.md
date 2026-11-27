# Матрица функционального покрытия

Браузерные и HTTP-действия ниже опираются на наблюдаемое поведение. Для остальной таблицы источник — динамический Django URL resolver. Регистрация маршрута доказывает наличие обработчика, а проверка всех его ролей и комбинаций данных требует отдельного прогона.

| Функция | URL или endpoint | Роль | Данные | Positive | Negative | Ожидание | Фактический результат | Статус | Evidence | Regression |
|---|---|---|---|---|---|---|---|---|---|---|
| Локальный вход | /login | SecOps, Reader | Четыре синтетических аккаунта | Отправить форму | Очистить session cookie | Сессия выдаётся, прямой маршрут без cookie ведёт на login | Chromium | PASS | browser-results.json | browser/qa.cjs |
| Список Projects | /workspace/projects | SecOps, Reader | Два проекта, 0/1/2 grants | Искать Payments, вернуться Back | Искать отсутствующий проект | Один результат по имени, empty state, соблюдение grants | Chromium | PASS | browser-results.json | browser/qa.cjs |
| Classic native API | /api/v2/import-scan/ | SecOps API token | Отдельный синтетический Product | Import и reimport, затем Finding PATCH и повторный GET | Проверка всей матрицы denied открыта | 201/201, тот же Test, сохранены False Positive и Active | PASS | PASS | classic-results.json | test_aspm_ingestion.py |
| Classic Product Type | /organization/add | SecOps | Новый синтетический Product Type | Заполнить и сохранить | Проверка каждой ошибки валидации открыта | Запись видна после перехода в список | Chromium | PASS | browser-results.json | browser/qa.cjs |
| Переключение Reports | /workspace/reports | SecOps | Синтетические отчёты | Открыть все три вкладки и поиск | Проверка полной матрицы denied открыта | Тип и фильтр меняют раздел | Chromium | PASS | browser-results.json | browser/qa.cjs |
| System Health | /workspace/system-health | SecOps, Reader | Отдельные PostgreSQL, Valkey, private volume | Открыть dependency checks | Reader получает 403; неверный путь отображается unavailable | Доступ и состояния зависимостей | Chromium и Django | PASS | browser-results.json; django-focused-final.log | test_aspm_access.py |
| Scan Processing | /workspace/scan-processing | SecOps, Reader | Тестовые ScanRun | Открыть список | Поиск чужого проекта в Django | Показываются разрешённые сканы | Chromium и Django | PASS | browser-results.json; django-focused-final.log | test_aspm_access.py |
| Приём шести scanner reports | /api/aspm/v1/scans/ | Scoped CI | Форматы и файлы из SCANNER_COMPATIBILITY | Принять, дождаться Celery, повторить | Malformed fixture и scope чужого проекта | 202, COMPLETED, 200 для повтора, FAILED для некорректного файла | 6/6 форматов, 55 HTTP-запросов, 2 завершённых версий отчёта | PASS | api-results.json | test_aspm_scanner_compatibility.py |
| Original artifact | /api/aspm/v1/scans/<id>/artifact/ | Scoped CI | Файл, завершённый ScanRun | Побайтово сверить SHA-256 | Токен другого проекта | 200 с ожидаемым SHA-256, 404 для чужого проекта | 6 проверенных форматов | PASS | api-results.json | test_aspm_object_storage.py |
| Версии отчёта | /api/aspm/v1/commits/<id>/reports/ | Scoped CI | Шесть completed scans на одном коммите | Создать, скачать HTML/JSON, добавить поздний scan | Генерация из чужих сканов покрывается не целиком | Две версии, байты старого отчёта сохранены | 2 версии | PASS | api-results.json | test_aspm_zero_finalize.py |

## Инвентарь маршрутов

896 записей URL resolver, 857 уникальных выражений путей, 389 уникальных обработчиков. Из них 509 записи в ветке /api/. DRF сообщил 824 сопоставлений HTTP-методов с действиями.
 Матрица ниже учитывает маршрут как самостоятельный контракт. Статус выполнения конкретных операций указан в строках выше. Значения обработчика и declared actions взяты из resolver. Regex-маршруты и варианты форматов сохранены.

| URL matcher | Имя | Handler | Методы DRF | Роли / данные | Positive / Negative | Ожидание / факт | Статус / evidence |
|---|---|---|---|---|---|---|---|
| `/history/(?P<cid>\d+)/(?P<oid>\d+)$` | action_history | `dojo.auditlog.ui.views.action_history` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset$` | product | `dojo.product.ui.views.product` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)$` | view_product | `dojo.product.ui.views.view_product` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/components$` | view_product_components | `dojo.product.ui.views.view_product_components` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/engagements$` | view_engagements | `dojo.product.ui.views.view_engagements` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<product_id>\d+)/import_scan_results$` | import_scan_results_prod | `dojo.engagement.ui.views.ImportScanResultsView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/metrics$` | view_product_metrics | `dojo.product.ui.views.view_product_metrics` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/async_burndown_metrics$` | async_burndown_metrics | `dojo.product.ui.views.async_burndown_metrics` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/edit$` | edit_product | `dojo.product.ui.views.edit_product` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/delete$` | delete_product | `dojo.product.ui.views.delete_product` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/add` | new_product | `dojo.product.ui.views.new_product` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/new_engagement$` | new_eng_for_prod | `dojo.product.ui.views.new_eng_for_app` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/new_technology$` | new_tech_for_prod | `dojo.product.ui.views.new_tech_for_prod` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/technology/(?P<tid>\d+)/edit$` | edit_technology | `dojo.product.ui.views.edit_technology` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/technology/(?P<tid>\d+)/delete$` | delete_technology | `dojo.product.ui.views.delete_technology` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/new_engagement/cicd$` | new_eng_for_prod_cicd | `dojo.product.ui.views.new_eng_for_app_cicd` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/add_meta_data$` | add_meta_data | `dojo.product.ui.views.manage_meta_data` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/edit_notifications$` | edit_notifications | `dojo.product.ui.views.edit_notifications` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/edit_meta_data$` | edit_meta_data | `dojo.product.ui.views.manage_meta_data` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<product_id>\d+)/ad_hoc_finding$` | ad_hoc_finding | `dojo.product.ui.views.AdHocFindingView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/engagement_presets$` | engagement_presets | `dojo.product.ui.views.engagement_presets` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/engagement_presets/(?P<eid>\d+)/edit$` | edit_engagement_presets | `dojo.product.ui.views.edit_engagement_presets` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/engagement_presets/add$` | add_engagement_presets | `dojo.product.ui.views.add_engagement_presets` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/engagement_presets/(?P<eid>\d+)/delete$` | delete_engagement_presets | `dojo.product.ui.views.delete_engagement_presets` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/authorized_users/add$` | add_product_authorized_users | `dojo.product.ui.views.add_product_authorized_users` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/authorized_users/(?P<user_id>\d+)/delete$` | delete_product_authorized_user | `dojo.product.ui.views.delete_product_authorized_user` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/add_api_scan_configuration$` | add_api_scan_configuration | `dojo.product.ui.views.add_api_scan_configuration` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/view_api_scan_configurations$` | view_api_scan_configurations | `dojo.product.ui.views.view_api_scan_configurations` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/edit_api_scan_configuration/(?P<pascid>\d+)$` | edit_api_scan_configuration | `dojo.product.ui.views.edit_api_scan_configuration` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/delete_api_scan_configuration/(?P<pascid>\d+)$` | delete_api_scan_configuration | `dojo.product.ui.views.delete_api_scan_configuration` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/components$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/engagements$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<product_id>\d+)/import_scan_results$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/metrics$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/async_burndown_metrics$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/edit$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/delete$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/add` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/new_engagement$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/new_technology$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/new_engagement/cicd$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/add_meta_data$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/edit_notifications$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/edit_meta_data$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<product_id>\d+)/ad_hoc_finding$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/engagement_presets$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/engagement_presets/(?P<eid>\d+)/edit$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/engagement_presets/add$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/engagement_presets/(?P<eid>\d+)/delete$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/authorized_users/add$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/authorized_users/(?P<user_id>\d+)/delete$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/add_api_scan_configuration$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/view_api_scan_configurations$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/edit_api_scan_configuration/(?P<pascid>\d+)$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/delete_api_scan_configuration/(?P<pascid>\d+)$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/dev_env$` | dev_env | `dojo.development_environment.ui.views.dev_env` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/dev_env/add$` | add_dev_env | `dojo.development_environment.ui.views.add_dev_env` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/dev_env/(?P<deid>\d+)/edit$` | edit_dev_env | `dojo.development_environment.ui.views.edit_dev_env` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product_platform$` | product_platforms | `dojo.product_attributes.ui.views.list_platforms` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product_platform/add$` | add_product_platform | `dojo.product_attributes.ui.views.add_platform` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product_platform/(?P<pk>\d+)/edit$` | edit_product_platform | `dojo.product_attributes.ui.views.edit_platform` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product_lifecycle$` | product_lifecycles | `dojo.product_attributes.ui.views.list_lifecycles` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product_lifecycle/add$` | add_product_lifecycle | `dojo.product_attributes.ui.views.add_lifecycle` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product_lifecycle/(?P<pk>\d+)/edit$` | edit_product_lifecycle | `dojo.product_attributes.ui.views.edit_lifecycle` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product_origin$` | product_origins | `dojo.product_attributes.ui.views.list_origins` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product_origin/add$` | add_product_origin | `dojo.product_attributes.ui.views.add_origin` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product_origin/(?P<pk>\d+)/edit$` | edit_product_origin | `dojo.product_attributes.ui.views.edit_origin` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/calendar$` | calendar | `dojo.engagement.ui.views.engagement_calendar` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/calendar/engagements$` | engagement_calendar | `dojo.engagement.ui.views.engagement_calendar` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement$` | engagement | `dojo.engagement.ui.views.engagements` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagements_all$` | engagements_all | `dojo.engagement.ui.views.engagements_all` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/all$` | all_engagements | `dojo.engagement.ui.views.engagements` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/active$` | active_engagements | `dojo.engagement.ui.views.engagements` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)$` | view_engagement | `dojo.engagement.ui.views.ViewEngagement` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/ics$` | engagement_ics | `dojo.engagement.ui.views.engagement_ics` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/edit$` | edit_engagement | `dojo.engagement.ui.views.edit_engagement` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/delete$` | delete_engagement | `dojo.engagement.ui.views.delete_engagement` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/copy$` | copy_engagement | `dojo.engagement.ui.views.copy_engagement` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/add_tests$` | add_tests | `dojo.engagement.ui.views.add_tests` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<engagement_id>\d+)/import_scan_results$` | import_scan_results | `dojo.engagement.ui.views.ImportScanResultsView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/close$` | close_engagement | `dojo.engagement.ui.views.close_eng` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/reopen$` | reopen_engagement | `dojo.engagement.ui.views.reopen_eng` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/jira/unlink$` | engagement_unlink_jira | `dojo.engagement.ui.views.unlink_jira` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/complete_checklist$` | complete_checklist | `dojo.engagement.ui.views.complete_checklist` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/risk_acceptance/add$` | add_risk_acceptance | `dojo.engagement.ui.views.add_risk_acceptance` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/risk_acceptance/add/(?P<fid>\d+)$` | add_risk_acceptance | `dojo.engagement.ui.views.add_risk_acceptance` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/risk_acceptance/(?P<raid>\d+)$` | view_risk_acceptance | `dojo.engagement.ui.views.view_risk_acceptance` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/risk_acceptance/(?P<raid>\d+)/edit$` | edit_risk_acceptance | `dojo.engagement.ui.views.edit_risk_acceptance` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/risk_acceptance/(?P<raid>\d+)/expire$` | expire_risk_acceptance | `dojo.engagement.ui.views.expire_risk_acceptance` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/risk_acceptance/(?P<raid>\d+)/reinstate$` | reinstate_risk_acceptance | `dojo.engagement.ui.views.reinstate_risk_acceptance` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/risk_acceptance/(?P<raid>\d+)/delete$` | delete_risk_acceptance | `dojo.engagement.ui.views.delete_risk_acceptance` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/risk_acceptance/(?P<raid>\d+)/download$` | download_risk_acceptance | `dojo.engagement.ui.views.download_risk_acceptance` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/threatmodel$` | view_threatmodel | `dojo.engagement.ui.views.view_threatmodel` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/threatmodel/upload$` | upload_threatmodel | `dojo.engagement.ui.views.upload_threatmodel` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/csv_export$` | engagement_csv_export | `dojo.engagement.ui.views.csv_export` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/excel_export$` | engagement_excel_export | `dojo.engagement.ui.views.excel_export` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<finding_id>\d+)$` | view_finding | `dojo.finding.ui.views.ViewFinding` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<finding_id>\d+)/edit$` | edit_finding | `dojo.finding.ui.views.EditFinding` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<finding_id>\d+)/delete$` | delete_finding | `dojo.finding.ui.views.DeleteFinding` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding$` | all_findings | `dojo.finding.ui.views.ListFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/open$` | open_findings | `dojo.finding.ui.views.ListOpenFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/verified$` | verified_findings | `dojo.finding.ui.views.ListVerifiedFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/closed$` | closed_findings | `dojo.finding.ui.views.ListClosedFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/accepted$` | accepted_findings | `dojo.finding.ui.views.ListAcceptedFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<product_id>\d+)/finding/open$` | product_open_findings | `dojo.finding.ui.views.ListOpenFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<product_id>\d+)/findings$` | view_product_findings_old | `dojo.finding.ui.views.ListOpenFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<product_id>\d+)/finding/verified$` | product_verified_findings | `dojo.finding.ui.views.ListVerifiedFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<product_id>\d+)/finding/out_of_scope$` | product_out_of_scope_findings | `dojo.finding.ui.views.ListOutOfScopeFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<product_id>\d+)/finding/inactive$` | product_inactive_findings | `dojo.finding.ui.views.ListInactiveFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<product_id>\d+)/finding/all$` | product_all_findings | `dojo.finding.ui.views.ListFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<product_id>\d+)/finding/closed$` | product_closed_findings | `dojo.finding.ui.views.ListClosedFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<product_id>\d+)/finding/false_positive$` | product_false_positive_findings | `dojo.finding.ui.views.ListFalsePositiveFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<product_id>\d+)/finding/accepted$` | product_accepted_findings | `dojo.finding.ui.views.ListAcceptedFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<engagement_id>\d+)/finding/open$` | engagement_open_findings | `dojo.finding.ui.views.ListOpenFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<engagement_id>\d+)/finding/closed$` | engagement_closed_findings | `dojo.finding.ui.views.ListClosedFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<engagement_id>\d+)/finding/verified$` | engagement_verified_findings | `dojo.finding.ui.views.ListVerifiedFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<engagement_id>\d+)/finding/accepted$` | engagement_accepted_findings | `dojo.finding.ui.views.ListAcceptedFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<engagement_id>\d+)/finding/all$` | engagement_all_findings | `dojo.finding.ui.views.ListFindings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/bulk$` | finding_bulk_update_all | `dojo.finding.ui.views.finding_bulk_update_all` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/finding/bulk_product$` | finding_bulk_update_all_product | `dojo.finding.ui.views.finding_bulk_update_all` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<fid>\d+)/touch$` | touch_finding | `dojo.finding.ui.views.touch_finding` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<fid>\d+)/simple_risk_accept$` | simple_risk_accept_finding | `dojo.finding.ui.views.simple_risk_accept` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<fid>\d+)/simple_risk_unaccept$` | risk_unaccept_finding | `dojo.finding.ui.views.risk_unaccept` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<fid>\d+)/request_review$` | request_finding_review | `dojo.finding.ui.views.request_finding_review` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<fid>\d+)/review$` | clear_finding_review | `dojo.finding.ui.views.clear_finding_review` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<fid>\d+)/copy$` | copy_finding | `dojo.finding.ui.views.copy_finding` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<fid>\d+)/mktemplate$` | mktemplate | `dojo.finding.ui.views.mktemplate` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<fid>\d+)/find_template_to_apply$` | find_template_to_apply | `dojo.finding.ui.views.find_template_to_apply` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<tid>\d+)/(?P<fid>\d+)/choose_finding_template_options$` | choose_finding_template_options | `dojo.finding.ui.views.choose_finding_template_options` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<fid>\d+)/(?P<tid>\d+)/apply_template_to_finding$` | apply_template_to_finding | `dojo.finding.ui.views.apply_template_to_finding` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<fid>\d+)/verify$` | verify_finding | `dojo.finding.ui.views.verify_finding` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<fid>\d+)/close$` | close_finding | `dojo.finding.ui.views.close_finding` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<fid>\d+)/defect_review$` | defect_finding_review | `dojo.finding.ui.views.defect_finding_review` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<fid>\d+)/open$` | reopen_finding | `dojo.finding.ui.views.reopen_finding` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/image/(?P<token>[^/]+)$` | download_finding_pic | `dojo.finding.ui.views.download_finding_pic` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<pid>\d+)/merge$` | merge_finding | `dojo.finding.ui.views.merge_finding_product` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/merge$` | merge_finding_product | `dojo.finding.ui.views.merge_finding_product` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<duplicate_id>\d+)/duplicate/(?P<original_id>\d+)$` | mark_finding_duplicate | `dojo.finding.ui.views.mark_finding_duplicate` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<duplicate_id>\d+)/duplicate/reset$` | reset_finding_duplicate_status | `dojo.finding.ui.views.reset_finding_duplicate_status` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<finding_id>\d+)/original/(?P<new_original_id>\d+)$` | set_finding_as_original | `dojo.finding.ui.views.set_finding_as_original` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<fid>\d+)/remediation_date$` | remediation_date | `dojo.finding.ui.views.remediation_date` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/template$` | templates | `dojo.finding.ui.views.templates` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/template/add$` | add_template | `dojo.finding.ui.views.add_template` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/template/(?P<tid>\d+)/edit$` | edit_template | `dojo.finding.ui.views.edit_template` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/template/(?P<tid>\d+)/delete$` | delete_template | `dojo.finding.ui.views.delete_template` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/template/export$` | export_template | `dojo.finding.ui.views.export_templates_to_json` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<fid>\d+)/jira/unlink$` | finding_unlink_jira | `dojo.finding.ui.views.unlink_jira` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding/(?P<fid>\d+)/jira/push$` | finding_push_to_jira | `dojo.finding.ui.views.push_to_jira` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding_group/(?P<fgid>\d+)$` | view_finding_group | `dojo.finding_group.views.view_finding_group` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding_group/(?P<fgid>\d+)/delete$` | delete_finding_group | `dojo.finding_group.views.delete_finding_group` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding_group/(?P<fgid>\d+)/jira/push$` | finding_group_push_to_jira | `dojo.finding_group.views.push_to_jira` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding_group/(?P<fgid>\d+)/jira/unlink$` | finding_group_unlink_jira | `dojo.finding_group.views.unlink_jira` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding_group/all$` | all_finding_groups | `dojo.finding_group.views.ListFindingGroups` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding_group/open$` | open_finding_groups | `dojo.finding_group.views.ListOpenFindingGroups` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/finding_group/closed$` | closed_finding_groups | `dojo.finding_group.views.ListClosedFindingGroups` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/$` | home | `dojo.home.views.home` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/dashboard$` | dashboard | `dojo.home.views.dashboard` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/support$` | support | `dojo.home.views.support` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/metrics$` | metrics | `dojo.metrics.views.metrics` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/critical_asset_metrics$` | critical_product_metrics | `dojo.metrics.views.critical_product_metrics` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/metrics/all$` | metrics_all | `dojo.metrics.views.metrics` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/metrics/organization$` | metrics_product_type | `dojo.metrics.views.metrics` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/metrics/simple$` | simple_metrics | `dojo.metrics.views.simple_metrics` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/metrics/organization/(?P<mtype>\d+)$` | product_type_metrics | `dojo.metrics.views.metrics` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/metrics/organization/counts$` | product_type_counts | `dojo.metrics.views.product_type_counts` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/metrics/asset/tag/counts$` | product_tag_counts | `dojo.metrics.views.product_tag_counts` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/metrics/engineer$` | engineer_metrics | `dojo.metrics.views.engineer_metrics` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/metrics/engineer/(?P<eid>\d+)$` | view_engineer | `dojo.metrics.views.view_engineer` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/critical_product_metrics$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/metrics/product/type$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/metrics/product/type/(?P<mtype>\d+)$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/metrics/product/type/counts$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/metrics/product/tag/counts$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/organization$` | product_type | `dojo.product_type.ui.views.product_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/organization/(?P<ptid>\d+)$` | view_product_type | `dojo.product_type.ui.views.view_product_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/organization/(?P<ptid>\d+)/edit$` | edit_product_type | `dojo.product_type.ui.views.edit_product_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/organization/(?P<ptid>\d+)/delete$` | delete_product_type | `dojo.product_type.ui.views.delete_product_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/organization/add$` | add_product_type | `dojo.product_type.ui.views.add_product_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/organization/(?P<ptid>\d+)/add_asset` | add_product_to_product_type | `dojo.product.ui.views.new_product` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/organization/(?P<ptid>\d+)/authorized_users/add$` | add_product_type_authorized_users | `dojo.product_type.ui.views.add_product_type_authorized_users` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/organization/(?P<ptid>\d+)/authorized_users/(?P<user_id>\d+)/delete$` | delete_product_type_authorized_user | `dojo.product_type.ui.views.delete_product_type_authorized_user` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/type$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/type/(?P<ptid>\d+)$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/type/(?P<ptid>\d+)/edit$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/type/(?P<ptid>\d+)/delete$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/type/add$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/type/(?P<ptid>\d+)/add_product` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/type/(?P<ptid>\d+)/authorized_users/add$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/type/(?P<ptid>\d+)/authorized_users/(?P<user_id>\d+)/delete$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/organization/(?P<ptid>\d+)/report$` | product_type_report | `dojo.reports.ui.views.product_type_report` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/report$` | product_report | `dojo.reports.ui.views.product_report` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/(?P<pid>\d+)/endpoint/report$` | product_endpoint_report | `dojo.reports.ui.views.product_endpoint_report` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/report$` | engagement_report | `dojo.reports.ui.views.engagement_report` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/test/(?P<tid>\d+)/report$` | test_report | `dojo.reports.ui.views.test_report` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/asset/report$` | product_findings_report | `dojo.reports.ui.views.product_findings_report` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/reports/cover$` | report_cover_page | `dojo.reports.ui.views.report_cover_page` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/reports/builder$` | report_builder | `dojo.reports.ui.views.ReportBuilder` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/reports/findings$` | report_findings | `dojo.reports.ui.views.report_findings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/reports/endpoints$` | report_endpoints | `dojo.reports.ui.views.report_endpoints` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/reports/custom$` | custom_report | `dojo.reports.ui.views.CustomReport` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/reports/quick$` | quick_report | `dojo.reports.ui.views.QuickReportView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/reports/csv_export$` | csv_export | `dojo.reports.ui.views.CSVExportView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/reports/excel_export$` | excel_export | `dojo.reports.ui.views.ExcelExportView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/type/(?P<ptid>\d+)/report$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/report$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/endpoint/report$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/report$` | — | `dojo.utils.redirect_view.<locals>._redirect` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/simple_search$` | simple_search | `dojo.search.views.simple_search` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/test_type$` | test_type | `dojo.test_type.views.test_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/test_type/add$` | add_test_type | `dojo.test_type.views.add_test_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/test_type/(?P<ptid>\d+)/edit$` | edit_test_type | `dojo.test_type.views.edit_test_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/calendar/tests$` | test_calendar | `dojo.test.ui.views.test_calendar` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/test/(?P<test_id>\d+)$` | view_test | `dojo.test.ui.views.ViewTest` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/test/(?P<tid>\d+)/ics$` | test_ics | `dojo.test.ui.views.test_ics` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/test/(?P<tid>\d+)/edit$` | edit_test | `dojo.test.ui.views.edit_test` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/test/(?P<tid>\d+)/delete$` | delete_test | `dojo.test.ui.views.delete_test` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/test/(?P<tid>\d+)/copy$` | copy_test | `dojo.test.ui.views.copy_test` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/test/(?P<test_id>\d+)/add_findings$` | add_findings | `dojo.test.ui.views.AddFindingView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/test/(?P<tid>\d+)/add_findings/(?P<fid>\d+)$` | add_finding_from_template | `dojo.test.ui.views.add_finding_from_template` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/test/(?P<tid>\d+)/search$` | search | `dojo.test.ui.views.search` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/test/(?P<test_id>\d+)/re_import_scan_results` | re_import_scan_results | `dojo.test.ui.views.ReImportScanResultsView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/login$` | login | `dojo.user.ui.views.login_view` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/logout$` | logout | `dojo.user.ui.views.logout_view` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/alerts$` | alerts | `dojo.user.ui.views.alerts` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/alerts/json$` | alerts_json | `dojo.user.ui.views.alerts_json` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/alerts/count$` | alertcount | `dojo.user.ui.views.alertcount` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/alerts/count/text$` | alertcount_text | `dojo.user.ui.views.alertcount_text` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/alerts/partial$` | alerts_partial | `dojo.user.ui.views.alerts_partial` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/delete_alerts$` | delete_alerts | `dojo.user.ui.views.delete_alerts` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/profile$` | view_profile | `dojo.user.ui.views.view_profile` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/change_password$` | change_password | `dojo.user.ui.views.change_password` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/user$` | users | `dojo.user.ui.views.user` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/user/add$` | add_user | `dojo.user.ui.views.add_user` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/user/(?P<uid>\d+)$` | view_user | `dojo.user.ui.views.view_user` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/user/(?P<uid>\d+)/edit$` | edit_user | `dojo.user.ui.views.edit_user` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/user/(?P<uid>\d+)/delete` | delete_user | `dojo.user.ui.views.delete_user` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/user/(?P<uid>\d+)/authorize_products$` | authorize_user_for_products | `dojo.user.ui.views.authorize_user_for_products` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/user/(?P<uid>\d+)/authorize_product_types$` | authorize_user_for_product_types | `dojo.user.ui.views.authorize_user_for_product_types` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/user/(?P<uid>\d+)/revoke_product/(?P<pid>\d+)$` | revoke_user_from_product | `dojo.user.ui.views.revoke_user_from_product` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/user/(?P<uid>\d+)/revoke_product_type/(?P<ptid>\d+)$` | revoke_user_from_product_type | `dojo.user.ui.views.revoke_user_from_product_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/user/(?P<uid>\d+)/edit_permissions$` | edit_user_permissions | `dojo.user.ui.views.edit_permissions` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/password_reset/$` | password_reset | `dojo.user.ui.views.DojoPasswordResetView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/password_reset/done/$` | password_reset_done | `django.contrib.auth.views.PasswordResetDoneView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,40})/$` | password_reset_confirm | `dojo.user.ui.views.DojoPasswordResetConfirmView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/reset/done/$` | password_reset_complete | `django.contrib.auth.views.PasswordResetCompleteView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/forgot_username_done/$` | forgot_username_done | `django.contrib.auth.views.PasswordResetDoneView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/forgot_username/$` | forgot_username | `dojo.user.ui.views.DojoForgotUsernameView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/key-v2$` | api_v2_key | `dojo.user.ui.views.api_v2_key` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/webhook/(?P<secret>[\w-]+)$` | web_hook_secret | `dojo.jira.views.webhook` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/webhook/` | web_hook | `dojo.jira.views.webhook` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/jira/webhook/(?P<secret>[\w-]+)$` | jira_web_hook_secret | `dojo.jira.views.webhook` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/jira/webhook/` | jira_web_hook | `dojo.jira.views.webhook` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/jira/add` | add_jira | `dojo.jira.views.NewJiraView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/jira/advanced` | add_jira_advanced | `dojo.jira.views.AdvancedJiraView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/jira/(?P<jid>\d+)/edit$` | edit_jira | `dojo.jira.views.EditJiraView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/jira/(?P<tid>\d+)/delete$` | delete_jira | `dojo.jira.views.DeleteJiraView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/jira$` | jira | `dojo.jira.views.ListJiraView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/github-webhook` | github_web_hook | `dojo.github.ui.views.webhook` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/github/add` | add_github | `dojo.github.ui.views.new_github` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/github/(?P<tid>\d+)/delete$` | delete_github | `dojo.github.ui.views.delete_github` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/github$` | github | `dojo.github.ui.views.github` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/tool_type/add` | add_tool_type | `dojo.tool_type.ui.views.new_tool_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/tool_type/(?P<ttid>\d+)/edit$` | edit_tool_type | `dojo.tool_type.ui.views.edit_tool_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/tool_type$` | tool_type | `dojo.tool_type.ui.views.tool_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/tool_config/add` | add_tool_config | `dojo.tool_config.ui.views.new_tool_config` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/tool_config/(?P<ttid>\d+)/edit$` | edit_tool_config | `dojo.tool_config.ui.views.edit_tool_config` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/tool_config$` | tool_config | `dojo.tool_config.ui.views.tool_config` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/tool_product/add$` | new_tool_product | `dojo.tool_product.ui.views.new_tool_product` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/tool_product/all$` | all_tool_product | `dojo.tool_product.ui.views.all_tool_product` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/tool_product/(?P<ttid>\d+)/edit$` | edit_tool_product | `dojo.tool_product.ui.views.edit_tool_product` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/tool_product/(?P<ttid>\d+)/delete$` | delete_tool_product | `dojo.tool_product.ui.views.delete_tool_product` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/cicd_infrastructure/add$` | add_cicd_infrastructure | `dojo.cicd_infrastructure.ui.views.new_cicd_infrastructure` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/cicd_infrastructure/(?P<ciid>\d+)/edit$` | edit_cicd_infrastructure | `dojo.cicd_infrastructure.ui.views.edit_cicd_infrastructure` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/cicd_infrastructure/(?P<ciid>\d+)/delete$` | delete_cicd_infrastructure | `dojo.cicd_infrastructure.ui.views.delete_cicd_infrastructure` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/cicd_infrastructure$` | cicd_infrastructure | `dojo.cicd_infrastructure.ui.views.cicd_infrastructure` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/sla_config/add` | new_sla_config | `dojo.sla_config.views.new_sla_config` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/sla_config/(?P<slaid>\d+)/edit$` | edit_sla_config | `dojo.sla_config.views.edit_sla_config` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/sla_config$` | sla_config | `dojo.sla_config.views.sla_config` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/system_settings$` | system_settings | `dojo.system_settings.ui.views.SystemSettingsView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/celery_status$` | celery_status | `dojo.system_settings.ui.views.CeleryStatusView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/notifications$` | notifications | `dojo.notifications.ui.views.PersonalNotificationsView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/notifications/system$` | system_notifications | `dojo.notifications.ui.views.SystemNotificationsView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/notifications/personal$` | personal_notifications | `dojo.notifications.ui.views.PersonalNotificationsView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/notifications/template$` | template_notifications | `dojo.notifications.ui.views.TemplateNotificationsView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/notifications/webhooks$` | notification_webhooks | `dojo.notifications.ui.views.ListNotificationWebhooksView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/notifications/webhooks/add$` | add_notification_webhook | `dojo.notifications.ui.views.AddNotificationWebhooksView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/notifications/webhooks/(?P<nwhid>\d+)/edit$` | edit_notification_webhook | `dojo.notifications.ui.views.EditNotificationWebhooksView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/notifications/webhooks/(?P<nwhid>\d+)/delete$` | delete_notification_webhook | `dojo.notifications.ui.views.DeleteNotificationWebhooksView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/settings/integrations/webhooks/` | aspm_webhooks | `dojo.webhooks.ui.views.subscriptions` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/settings/integrations/webhooks/new/` | aspm_webhook_new | `dojo.webhooks.ui.views.edit` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/settings/integrations/webhooks/<int:pk>/edit/` | aspm_webhook_edit | `dojo.webhooks.ui.views.edit` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/settings/integrations/webhooks/<int:pk>/` | aspm_webhook_history | `dojo.webhooks.ui.views.history` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/settings/integrations/webhooks/<int:pk>/actions/<str:action>/` | aspm_webhook_action | `dojo.webhooks.ui.views.action` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/settings/integrations/webhooks/<int:pk>/deliveries/<uuid:delivery_id>/` | aspm_webhook_attempts | `dojo.webhooks.ui.views.attempts` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/settings/integrations/webhooks/<int:pk>/deliveries/<uuid:delivery_id>/replay/` | aspm_webhook_replay | `dojo.webhooks.ui.views.replay` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/sso/login` | aspm_oidc_login | `dojo.aspm_access.views.start` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/sso/callback` | aspm_oidc_callback | `dojo.aspm_access.views.callback` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/sso/logout` | aspm_oidc_logout | `dojo.aspm_access.views.end` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/workspace/classic` | aspm_classic | `dojo.aspm_access.workspace.classic` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/workspace/projects` | aspm_projects | `dojo.aspm_access.workspace.projects` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/workspace/reports` | aspm_reports | `dojo.aspm_access.workspace.reports` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/workspace/scan-processing` | aspm_scan_processing | `dojo.aspm_access.workspace.scan_processing` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/workspace/system-health` | aspm_system_health | `dojo.aspm_access.workspace.system_health` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/workspace/scanners` | aspm_scanners | `dojo.aspm_access.workspace.scanners` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/workspace/access` | aspm_sso_mappings | `dojo.aspm_access.workspace.sso_mappings` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/workspace/projects/<int:product_id>/engagement-policy` | aspm_engagement_policy | `dojo.aspm_access.workspace.engagement_policy` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/object/add$` | new_object | `dojo.object.ui.views.new_object` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/object/(?P<ttid>\d+)/edit$` | edit_object | `dojo.object.ui.views.edit_object` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/object/view$` | view_objects | `dojo.object.ui.views.view_objects` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<pid>\d+)/object/(?P<ttid>\d+)/delete$` | delete_object | `dojo.object.ui.views.delete_object` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/benchmark/(?P<pid>\d+)/type/(?P<benchmark_type>\d+)$` | view_product_benchmark | `dojo.benchmark.ui.views.benchmark_view` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/benchmark/(?P<pid>\d+)/type/(?P<benchmark_type>\d+)/category/(?P<cat>\d+)$` | view_product_benchmark | `dojo.benchmark.ui.views.benchmark_view` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/benchmark/(?P<pid>\d+)/type/(?P<benchmark_type>\d+)/category/(?P<cat>\d+)/edit/(?P<bid>\d+)$` | edit_benchmark | `dojo.benchmark.ui.views.benchmark_view` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/benchmark/(?P<pid>\d+)/type/(?P<benchmark_type>\d+)/delete$` | delete_product_benchmark | `dojo.benchmark.ui.views.delete` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/benchmark/(?P<pid>\d+)/type/(?P<_type>\d+)/update$` | update_product_benchmark | `dojo.benchmark.ui.views.update_benchmark` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/benchmark/(?P<pid>\d+)/type/(?P<_type>\d+)/summary/(?P<summary>\d+)/update$` | update_product_benchmark_summary | `dojo.benchmark.ui.views.update_benchmark_summary` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/notes/(?P<note_id>\d+)/delete/(?P<page>[\w-]+)/(?P<objid>\d+)$` | delete_note | `dojo.notes.ui.views.delete_note` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/notes/(?P<note_id>\d+)/edit/(?P<page>[\w-]+)/(?P<objid>\d+)$` | edit_note | `dojo.notes.ui.views.edit_note` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/notes/(?P<note_id>\d+)/history/(?P<page>[\w-]+)/(?P<objid>\d+)$` | note_history | `dojo.notes.ui.views.note_history` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/note_type$` | note_type | `dojo.note_type.ui.views.note_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/note/type/(?P<ntid>\d+)/edit$` | edit_note_type | `dojo.note_type.ui.views.edit_note_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/note/type/(?P<ntid>\d+)/disable$` | disable_note_type | `dojo.note_type.ui.views.disable_note_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/note/type/(?P<ntid>\d+)/enable$` | enable_note_type | `dojo.note_type.ui.views.enable_note_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/add_note_type$` | add_note_type | `dojo.note_type.ui.views.add_note_type` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/configure_banner$` | configure_banner | `dojo.banner.ui.views.configure_banner` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/components$` | components | `dojo.components.views.components` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/regulations/add` | new_regulation | `dojo.regulations.ui.views.new_regulation` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/regulations/(?P<ttid>\d+)/edit$` | edit_regulations | `dojo.regulations.ui.views.edit_regulations` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/regulations$` | regulations | `dojo.regulations.ui.views.regulations` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/configure_announcement$` | configure_announcement | `dojo.announcement.ui.views.configure_announcement` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/dismiss_announcement$` | dismiss_announcement | `dojo.announcement.ui.views.dismiss_announcement` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/dismiss_os_message$` | dismiss_os_message | `dojo.announcement.ui.views.dismiss_os_message` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/github_star_prompt$` | github_star_prompt | `dojo.announcement.ui.views.github_star_prompt` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/<int:product_id>/repositories` | scm_repository_list | `dojo.scm.ui.views.repository_list` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/repositories/<int:repository_id>` | scm_repository_detail | `dojo.scm.ui.views.repository_detail` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/commits/<int:commit_id>` | scm_commit_detail | `dojo.scm.ui.views.commit_detail` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/commits/<int:commit_id>/compare` | scm_commit_compare | `dojo.scm.ui.views.commit_compare` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/commits/<int:commit_id>/evidence` | aspm_commit_evidence | `dojo.aspm_ingestion.ui.views.commit_evidence` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/commits/<int:commit_id>/evidence/state` | aspm_commit_state | `dojo.aspm_ingestion.ui.views.commit_state` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/commits/<int:commit_id>/evidence/reports` | aspm_create_report | `dojo.aspm_ingestion.ui.views.create_report` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoint$` | endpoint | `dojo.url.ui.views.all_endpoints` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoint/host$` | endpoint_host | `dojo.url.ui.views.all_endpoint_hosts` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoint/vulnerable$` | vulnerable_endpoints | `dojo.url.ui.views.vulnerable_endpoints` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoint/host/vulnerable$` | vulnerable_endpoint_hosts | `dojo.url.ui.views.vulnerable_endpoint_hosts` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoint/(?P<location_id>\d+)$` | view_endpoint | `dojo.url.ui.views.view_endpoint` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoint/host/(?P<location_id>\d+)$` | view_endpoint_host | `dojo.url.ui.views.view_endpoint_host` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoint/(?P<location_id>\d+)/edit$` | edit_endpoint | `dojo.url.ui.views.edit_endpoint` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoints/product/(?P<product_id>\d+)/add$` | add_endpoint_to_product | `dojo.url.ui.views.add_endpoint_to_product` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoints/finding/(?P<finding_id>\d+)/add$` | add_endpoint_to_finding | `dojo.url.ui.views.add_endpoint_to_finding` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoints/product/(?P<product_id>\d+)/add$` | add_endpoint | `dojo.url.ui.views.add_endpoint_to_product` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoint/(?P<location_id>\d+)/delete$` | delete_endpoint | `dojo.url.ui.views.delete_endpoint` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoint/(?P<location_id>\d+)/add_meta_data$` | add_endpoint_meta_data | `dojo.url.ui.views.manage_meta_data` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoint/(?P<location_id>\d+)/edit_meta_data$` | edit_endpoint_meta_data | `dojo.url.ui.views.manage_meta_data` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoint/(?P<product_id>\d+)/import_endpoint_meta$` | import_endpoint_meta | `dojo.url.ui.views.import_endpoint_meta` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoint/bulk$` | endpoints_bulk_all | `dojo.url.ui.views.endpoint_bulk_update_all` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/product/(?P<product_id>\d+)/endpoint/bulk_product$` | endpoints_bulk_update_all_product | `dojo.url.ui.views.endpoint_bulk_update_all` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoint/(?P<finding_id>\d+)/bulk_status$` | endpoints_status_bulk | `dojo.url.ui.views.finding_location_bulk_update` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoint/migrate$` | endpoint_migrate | `dojo.url.ui.views.migrate_endpoints_view` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoint/(?P<location_id>\d+)/report$` | endpoint_report | `dojo.url.ui.views.endpoint_report` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/endpoint/host/(?P<location_id>\d+)/report$` | endpoint_host_report | `dojo.url.ui.views.endpoint_host_report` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/oa3/schema/` | schema_oa3 | `dojo.api_v2.views.DojoSpectacularAPIView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/oa3/swagger-ui/` | swagger-ui_oa3 | `drf_spectacular.views.SpectacularSwaggerView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/robots.txt` | robots_file | `dojo.urls.<lambda>` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/manage_files/(?P<oid>\d+)/(?P<obj_type>\w+)$` | manage_files | `dojo.views.manage_files` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/access_file/(?P<fid>\d+)/(?P<oid>\d+)/(?P<obj_type>\w+)$` | access_file | `dojo.views.access_file` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/media/(?P<path>.*)$` | — | `dojo.views.protected_serve` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/aspm/v1/openapi/` | aspm_v1:openapi | `drf_spectacular.views.SpectacularAPIView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/aspm/v1/scans/` | aspm_v1:scans | `dojo.aspm_ingestion.api.views.ScanUploadView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/aspm/v1/scans/<uuid:pk>/` | aspm_v1:scan-detail | `dojo.aspm_ingestion.api.views.ScanDetailView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/aspm/v1/scans/<uuid:pk>/retry/` | aspm_v1:scan-retry | `dojo.aspm_ingestion.api.views.ScanRetryView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/aspm/v1/scans/<uuid:pk>/artifact/` | aspm_v1:artifact | `dojo.aspm_ingestion.api.views.ArtifactDownloadView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/aspm/v1/projects/<int:pk>/repositories/` | aspm_v1:repositories | `dojo.aspm_ingestion.api.views.ProjectRepositoriesView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/aspm/v1/repositories/<int:pk>/commits/` | aspm_v1:commits | `dojo.aspm_ingestion.api.views.RepositoryCommitsView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/aspm/v1/commits/<int:pk>/scans/` | aspm_v1:commit-scans | `dojo.aspm_ingestion.api.views.CommitScansView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/aspm/v1/commits/<int:pk>/finalize/` | aspm_v1:finalize | `dojo.aspm_ingestion.api.views.FinalizeView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/aspm/v1/commits/<int:pk>/reports/` | aspm_v1:reports | `dojo.aspm_ingestion.api.views.CommitReportsView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/aspm/v1/reports/<uuid:pk>/download/` | aspm_v1:report-download | `dojo.aspm_ingestion.api.views.ReportDownloadView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/announcements/$` | announcement-list | `dojo.announcement.api.views.AnnouncementViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/announcements\.(?P<format>[a-z0-9]+)/?$` | announcement-list | `dojo.announcement.api.views.AnnouncementViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/announcements/(?P<pk>[^/.]+)/$` | announcement-detail | `dojo.announcement.api.views.AnnouncementViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/announcements/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | announcement-detail | `dojo.announcement.api.views.AnnouncementViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/announcements/(?P<pk>[^/.]+)/delete_preview/$` | announcement-delete-preview | `dojo.announcement.api.views.AnnouncementViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/announcements/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | announcement-delete-preview | `dojo.announcement.api.views.AnnouncementViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/configuration_permissions/$` | permission-list | `dojo.api_v2.views.ConfigurationPermissionViewSet` | GET list | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/configuration_permissions\.(?P<format>[a-z0-9]+)/?$` | permission-list | `dojo.api_v2.views.ConfigurationPermissionViewSet` | GET list | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/configuration_permissions/(?P<pk>[^/.]+)/$` | permission-detail | `dojo.api_v2.views.ConfigurationPermissionViewSet` | GET retrieve | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/configuration_permissions/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | permission-detail | `dojo.api_v2.views.ConfigurationPermissionViewSet` | GET retrieve | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/development_environments/$` | development_environment-list | `dojo.development_environment.api.views.DevelopmentEnvironmentViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/development_environments\.(?P<format>[a-z0-9]+)/?$` | development_environment-list | `dojo.development_environment.api.views.DevelopmentEnvironmentViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/development_environments/(?P<pk>[^/.]+)/$` | development_environment-detail | `dojo.development_environment.api.views.DevelopmentEnvironmentViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/development_environments/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | development_environment-detail | `dojo.development_environment.api.views.DevelopmentEnvironmentViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/development_environments/(?P<pk>[^/.]+)/delete_preview/$` | development_environment-delete-preview | `dojo.development_environment.api.views.DevelopmentEnvironmentViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/development_environments/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | development_environment-delete-preview | `dojo.development_environment.api.views.DevelopmentEnvironmentViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_platforms/$` | product_platform-list | `dojo.product_attributes.api.views.ProductPlatformViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_platforms\.(?P<format>[a-z0-9]+)/?$` | product_platform-list | `dojo.product_attributes.api.views.ProductPlatformViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_platforms/(?P<pk>[^/.]+)/$` | product_platform-detail | `dojo.product_attributes.api.views.ProductPlatformViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_platforms/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | product_platform-detail | `dojo.product_attributes.api.views.ProductPlatformViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_platforms/(?P<pk>[^/.]+)/delete_preview/$` | product_platform-delete-preview | `dojo.product_attributes.api.views.ProductPlatformViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_platforms/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | product_platform-delete-preview | `dojo.product_attributes.api.views.ProductPlatformViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_lifecycles/$` | product_lifecycle-list | `dojo.product_attributes.api.views.ProductLifecycleViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_lifecycles\.(?P<format>[a-z0-9]+)/?$` | product_lifecycle-list | `dojo.product_attributes.api.views.ProductLifecycleViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_lifecycles/(?P<pk>[^/.]+)/$` | product_lifecycle-detail | `dojo.product_attributes.api.views.ProductLifecycleViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_lifecycles/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | product_lifecycle-detail | `dojo.product_attributes.api.views.ProductLifecycleViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_lifecycles/(?P<pk>[^/.]+)/delete_preview/$` | product_lifecycle-delete-preview | `dojo.product_attributes.api.views.ProductLifecycleViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_lifecycles/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | product_lifecycle-delete-preview | `dojo.product_attributes.api.views.ProductLifecycleViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_origins/$` | product_origin-list | `dojo.product_attributes.api.views.ProductOriginViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_origins\.(?P<format>[a-z0-9]+)/?$` | product_origin-list | `dojo.product_attributes.api.views.ProductOriginViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_origins/(?P<pk>[^/.]+)/$` | product_origin-detail | `dojo.product_attributes.api.views.ProductOriginViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_origins/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | product_origin-detail | `dojo.product_attributes.api.views.ProductOriginViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_origins/(?P<pk>[^/.]+)/delete_preview/$` | product_origin-delete-preview | `dojo.product_attributes.api.views.ProductOriginViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_origins/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | product_origin-delete-preview | `dojo.product_attributes.api.views.ProductOriginViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/endpoint_meta_import/$` | endpointmetaimport-list | `dojo.endpoint.api.views.EndpointMetaImporterView` | POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/endpoint_meta_import\.(?P<format>[a-z0-9]+)/?$` | endpointmetaimport-list | `dojo.endpoint.api.views.EndpointMetaImporterView` | POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/import-languages/$` | importlanguages-list | `dojo.api_v2.views.ImportLanguagesView` | POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/import-languages\.(?P<format>[a-z0-9]+)/?$` | importlanguages-list | `dojo.api_v2.views.ImportLanguagesView` | POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/import-scan/$` | importscan-list | `dojo.api_v2.views.ImportScanView` | POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/import-scan\.(?P<format>[a-z0-9]+)/?$` | importscan-list | `dojo.api_v2.views.ImportScanView` | POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_instances/$` | jira_instance-list | `dojo.jira.api.views.JiraInstanceViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_instances\.(?P<format>[a-z0-9]+)/?$` | jira_instance-list | `dojo.jira.api.views.JiraInstanceViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_instances/(?P<pk>[^/.]+)/$` | jira_instance-detail | `dojo.jira.api.views.JiraInstanceViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_instances/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | jira_instance-detail | `dojo.jira.api.views.JiraInstanceViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_instances/(?P<pk>[^/.]+)/delete_preview/$` | jira_instance-delete-preview | `dojo.jira.api.views.JiraInstanceViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_instances/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | jira_instance-delete-preview | `dojo.jira.api.views.JiraInstanceViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_configurations/$` | jira_configurations-list | `dojo.jira.api.views.JiraInstanceViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_configurations\.(?P<format>[a-z0-9]+)/?$` | jira_configurations-list | `dojo.jira.api.views.JiraInstanceViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_configurations/(?P<pk>[^/.]+)/$` | jira_configurations-detail | `dojo.jira.api.views.JiraInstanceViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_configurations/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | jira_configurations-detail | `dojo.jira.api.views.JiraInstanceViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_configurations/(?P<pk>[^/.]+)/delete_preview/$` | jira_configurations-delete-preview | `dojo.jira.api.views.JiraInstanceViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_configurations/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | jira_configurations-delete-preview | `dojo.jira.api.views.JiraInstanceViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_finding_mappings/$` | jira_issue-list | `dojo.jira.api.views.JiraIssuesViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_finding_mappings\.(?P<format>[a-z0-9]+)/?$` | jira_issue-list | `dojo.jira.api.views.JiraIssuesViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_finding_mappings/(?P<pk>[^/.]+)/$` | jira_issue-detail | `dojo.jira.api.views.JiraIssuesViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_finding_mappings/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | jira_issue-detail | `dojo.jira.api.views.JiraIssuesViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_finding_mappings/(?P<pk>[^/.]+)/delete_preview/$` | jira_issue-delete-preview | `dojo.jira.api.views.JiraIssuesViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_finding_mappings/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | jira_issue-delete-preview | `dojo.jira.api.views.JiraIssuesViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_product_configurations/$` | jira_product_configurations-list | `dojo.jira.api.views.JiraProjectViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_product_configurations\.(?P<format>[a-z0-9]+)/?$` | jira_product_configurations-list | `dojo.jira.api.views.JiraProjectViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_product_configurations/(?P<pk>[^/.]+)/$` | jira_product_configurations-detail | `dojo.jira.api.views.JiraProjectViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_product_configurations/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | jira_product_configurations-detail | `dojo.jira.api.views.JiraProjectViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_product_configurations/(?P<pk>[^/.]+)/delete_preview/$` | jira_product_configurations-delete-preview | `dojo.jira.api.views.JiraProjectViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_product_configurations/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | jira_product_configurations-delete-preview | `dojo.jira.api.views.JiraProjectViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_projects/$` | jira_project-list | `dojo.jira.api.views.JiraProjectViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_projects\.(?P<format>[a-z0-9]+)/?$` | jira_project-list | `dojo.jira.api.views.JiraProjectViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_projects/(?P<pk>[^/.]+)/$` | jira_project-detail | `dojo.jira.api.views.JiraProjectViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_projects/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | jira_project-detail | `dojo.jira.api.views.JiraProjectViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_projects/(?P<pk>[^/.]+)/delete_preview/$` | jira_project-delete-preview | `dojo.jira.api.views.JiraProjectViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/jira_projects/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | jira_project-delete-preview | `dojo.jira.api.views.JiraProjectViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/languages/$` | languages-list | `dojo.api_v2.views.LanguageViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/languages\.(?P<format>[a-z0-9]+)/?$` | languages-list | `dojo.api_v2.views.LanguageViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/languages/(?P<pk>[^/.]+)/$` | languages-detail | `dojo.api_v2.views.LanguageViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/languages/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | languages-detail | `dojo.api_v2.views.LanguageViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/languages/(?P<pk>[^/.]+)/delete_preview/$` | languages-delete-preview | `dojo.api_v2.views.LanguageViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/languages/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | languages-delete-preview | `dojo.api_v2.views.LanguageViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/language_types/$` | language_type-list | `dojo.api_v2.views.LanguageTypeViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/language_types\.(?P<format>[a-z0-9]+)/?$` | language_type-list | `dojo.api_v2.views.LanguageTypeViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/language_types/(?P<pk>[^/.]+)/$` | language_type-detail | `dojo.api_v2.views.LanguageTypeViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/language_types/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | language_type-detail | `dojo.api_v2.views.LanguageTypeViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/language_types/(?P<pk>[^/.]+)/delete_preview/$` | language_type-delete-preview | `dojo.api_v2.views.LanguageTypeViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/language_types/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | language_type-delete-preview | `dojo.api_v2.views.LanguageTypeViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/metadata/$` | metadata-list | `dojo.api_v2.views.DojoMetaViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/metadata\.(?P<format>[a-z0-9]+)/?$` | metadata-list | `dojo.api_v2.views.DojoMetaViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/metadata/batch/$` | metadata-batch | `dojo.api_v2.views.DojoMetaViewSet` | POST batch, PATCH batch | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/metadata/batch\.(?P<format>[a-z0-9]+)/?$` | metadata-batch | `dojo.api_v2.views.DojoMetaViewSet` | POST batch, PATCH batch | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/metadata/(?P<pk>[^/.]+)/$` | metadata-detail | `dojo.api_v2.views.DojoMetaViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/metadata/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | metadata-detail | `dojo.api_v2.views.DojoMetaViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/metadata/(?P<pk>[^/.]+)/delete_preview/$` | metadata-delete-preview | `dojo.api_v2.views.DojoMetaViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/metadata/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | metadata-delete-preview | `dojo.api_v2.views.DojoMetaViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/network_locations/$` | network_locations-list | `dojo.api_v2.views.NetworkLocationsViewset` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/network_locations\.(?P<format>[a-z0-9]+)/?$` | network_locations-list | `dojo.api_v2.views.NetworkLocationsViewset` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/network_locations/(?P<pk>[^/.]+)/$` | network_locations-detail | `dojo.api_v2.views.NetworkLocationsViewset` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/network_locations/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | network_locations-detail | `dojo.api_v2.views.NetworkLocationsViewset` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/network_locations/(?P<pk>[^/.]+)/delete_preview/$` | network_locations-delete-preview | `dojo.api_v2.views.NetworkLocationsViewset` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/network_locations/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | network_locations-delete-preview | `dojo.api_v2.views.NetworkLocationsViewset` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/notes/$` | notes-list | `dojo.notes.api.views.NotesViewSet` | GET list | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/notes\.(?P<format>[a-z0-9]+)/?$` | notes-list | `dojo.notes.api.views.NotesViewSet` | GET list | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/notes/(?P<pk>[^/.]+)/$` | notes-detail | `dojo.notes.api.views.NotesViewSet` | GET retrieve, PUT update, PATCH partial_update | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/notes/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | notes-detail | `dojo.notes.api.views.NotesViewSet` | GET retrieve, PUT update, PATCH partial_update | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/note_type/$` | note_type-list | `dojo.note_type.api.views.NoteTypeViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/note_type\.(?P<format>[a-z0-9]+)/?$` | note_type-list | `dojo.note_type.api.views.NoteTypeViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/note_type/(?P<pk>[^/.]+)/$` | note_type-detail | `dojo.note_type.api.views.NoteTypeViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/note_type/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | note_type-detail | `dojo.note_type.api.views.NoteTypeViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/note_type/(?P<pk>[^/.]+)/delete_preview/$` | note_type-delete-preview | `dojo.note_type.api.views.NoteTypeViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/note_type/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | note_type-delete-preview | `dojo.note_type.api.views.NoteTypeViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/notifications/$` | notifications-list | `dojo.notifications.api.views.NotificationsViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/notifications\.(?P<format>[a-z0-9]+)/?$` | notifications-list | `dojo.notifications.api.views.NotificationsViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/notifications/(?P<pk>[^/.]+)/$` | notifications-detail | `dojo.notifications.api.views.NotificationsViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/notifications/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | notifications-detail | `dojo.notifications.api.views.NotificationsViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/notifications/(?P<pk>[^/.]+)/delete_preview/$` | notifications-delete-preview | `dojo.notifications.api.views.NotificationsViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/notifications/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | notifications-delete-preview | `dojo.notifications.api.views.NotificationsViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/notification_webhooks/$` | notification_webhooks-list | `dojo.notifications.api.views.NotificationWebhooksViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/notification_webhooks\.(?P<format>[a-z0-9]+)/?$` | notification_webhooks-list | `dojo.notifications.api.views.NotificationWebhooksViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/notification_webhooks/(?P<pk>[^/.]+)/$` | notification_webhooks-detail | `dojo.notifications.api.views.NotificationWebhooksViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/notification_webhooks/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | notification_webhooks-detail | `dojo.notifications.api.views.NotificationWebhooksViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/notification_webhooks/(?P<pk>[^/.]+)/delete_preview/$` | notification_webhooks-delete-preview | `dojo.notifications.api.views.NotificationWebhooksViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/notification_webhooks/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | notification_webhooks-delete-preview | `dojo.notifications.api.views.NotificationWebhooksViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/products/$` | product-list | `dojo.product.api.views.ProductViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/products\.(?P<format>[a-z0-9]+)/?$` | product-list | `dojo.product.api.views.ProductViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/products/(?P<pk>[^/.]+)/$` | product-detail | `dojo.product.api.views.ProductViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/products/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | product-detail | `dojo.product.api.views.ProductViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/products/(?P<pk>[^/.]+)/delete_preview/$` | product-delete-preview | `dojo.product.api.views.ProductViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/products/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | product-delete-preview | `dojo.product.api.views.ProductViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/products/(?P<pk>[^/.]+)/generate_report/$` | product-generate-report | `dojo.product.api.views.ProductViewSet` | POST generate_report | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/products/(?P<pk>[^/.]+)/generate_report\.(?P<format>[a-z0-9]+)/?$` | product-generate-report | `dojo.product.api.views.ProductViewSet` | POST generate_report | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_api_scan_configurations/$` | product_api_scan_configuration-list | `dojo.product.api.views.ProductAPIScanConfigurationViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_api_scan_configurations\.(?P<format>[a-z0-9]+)/?$` | product_api_scan_configuration-list | `dojo.product.api.views.ProductAPIScanConfigurationViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_api_scan_configurations/(?P<pk>[^/.]+)/$` | product_api_scan_configuration-detail | `dojo.product.api.views.ProductAPIScanConfigurationViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_api_scan_configurations/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | product_api_scan_configuration-detail | `dojo.product.api.views.ProductAPIScanConfigurationViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_api_scan_configurations/(?P<pk>[^/.]+)/delete_preview/$` | product_api_scan_configuration-delete-preview | `dojo.product.api.views.ProductAPIScanConfigurationViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_api_scan_configurations/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | product_api_scan_configuration-delete-preview | `dojo.product.api.views.ProductAPIScanConfigurationViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_types/$` | product_type-list | `dojo.product_type.api.views.ProductTypeViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_types\.(?P<format>[a-z0-9]+)/?$` | product_type-list | `dojo.product_type.api.views.ProductTypeViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_types/(?P<pk>[^/.]+)/$` | product_type-detail | `dojo.product_type.api.views.ProductTypeViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_types/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | product_type-detail | `dojo.product_type.api.views.ProductTypeViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_types/(?P<pk>[^/.]+)/delete_preview/$` | product_type-delete-preview | `dojo.product_type.api.views.ProductTypeViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_types/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | product_type-delete-preview | `dojo.product_type.api.views.ProductTypeViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_types/(?P<pk>[^/.]+)/generate_report/$` | product_type-generate-report | `dojo.product_type.api.views.ProductTypeViewSet` | POST generate_report | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/product_types/(?P<pk>[^/.]+)/generate_report\.(?P<format>[a-z0-9]+)/?$` | product_type-generate-report | `dojo.product_type.api.views.ProductTypeViewSet` | POST generate_report | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/$` | engagement-list | `dojo.engagement.api.views.EngagementViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements\.(?P<format>[a-z0-9]+)/?$` | engagement-list | `dojo.engagement.api.views.EngagementViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/$` | engagement-detail | `dojo.engagement.api.views.EngagementViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | engagement-detail | `dojo.engagement.api.views.EngagementViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/accept_risks/$` | engagement-accept-risks | `dojo.engagement.api.views.EngagementViewSet` | POST accept_risks | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/accept_risks\.(?P<format>[a-z0-9]+)/?$` | engagement-accept-risks | `dojo.engagement.api.views.EngagementViewSet` | POST accept_risks | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/close/$` | engagement-close | `dojo.engagement.api.views.EngagementViewSet` | POST close | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/close\.(?P<format>[a-z0-9]+)/?$` | engagement-close | `dojo.engagement.api.views.EngagementViewSet` | POST close | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/complete_checklist/$` | engagement-complete-checklist | `dojo.engagement.api.views.EngagementViewSet` | GET complete_checklist, POST complete_checklist | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/complete_checklist\.(?P<format>[a-z0-9]+)/?$` | engagement-complete-checklist | `dojo.engagement.api.views.EngagementViewSet` | GET complete_checklist, POST complete_checklist | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/delete_preview/$` | engagement-delete-preview | `dojo.engagement.api.views.EngagementViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | engagement-delete-preview | `dojo.engagement.api.views.EngagementViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/files/download/(?P<file_id>\d+)/$` | engagement-download-file | `dojo.engagement.api.views.EngagementViewSet` | GET download_file | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/files/download/(?P<file_id>\d+)\.(?P<format>[a-z0-9]+)/?$` | engagement-download-file | `dojo.engagement.api.views.EngagementViewSet` | GET download_file | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/files/$` | engagement-files | `dojo.engagement.api.views.EngagementViewSet` | GET files, POST files | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/files\.(?P<format>[a-z0-9]+)/?$` | engagement-files | `dojo.engagement.api.views.EngagementViewSet` | GET files, POST files | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/generate_report/$` | engagement-generate-report | `dojo.engagement.api.views.EngagementViewSet` | POST generate_report | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/generate_report\.(?P<format>[a-z0-9]+)/?$` | engagement-generate-report | `dojo.engagement.api.views.EngagementViewSet` | POST generate_report | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/notes/$` | engagement-notes | `dojo.engagement.api.views.EngagementViewSet` | GET notes, POST notes | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/notes\.(?P<format>[a-z0-9]+)/?$` | engagement-notes | `dojo.engagement.api.views.EngagementViewSet` | GET notes, POST notes | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/reopen/$` | engagement-reopen | `dojo.engagement.api.views.EngagementViewSet` | POST reopen | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/reopen\.(?P<format>[a-z0-9]+)/?$` | engagement-reopen | `dojo.engagement.api.views.EngagementViewSet` | POST reopen | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/update_jira_epic/$` | engagement-update-jira-epic | `dojo.engagement.api.views.EngagementViewSet` | POST update_jira_epic | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagements/(?P<pk>[^/.]+)/update_jira_epic\.(?P<format>[a-z0-9]+)/?$` | engagement-update-jira-epic | `dojo.engagement.api.views.EngagementViewSet` | POST update_jira_epic | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagement_presets/$` | engagement_presets-list | `dojo.engagement.api.views.EngagementPresetsViewset` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagement_presets\.(?P<format>[a-z0-9]+)/?$` | engagement_presets-list | `dojo.engagement.api.views.EngagementPresetsViewset` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagement_presets/(?P<pk>[^/.]+)/$` | engagement_presets-detail | `dojo.engagement.api.views.EngagementPresetsViewset` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagement_presets/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | engagement_presets-detail | `dojo.engagement.api.views.EngagementPresetsViewset` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagement_presets/(?P<pk>[^/.]+)/delete_preview/$` | engagement_presets-delete-preview | `dojo.engagement.api.views.EngagementPresetsViewset` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/engagement_presets/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | engagement_presets-delete-preview | `dojo.engagement.api.views.EngagementPresetsViewset` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/finding_templates/$` | finding_template-list | `dojo.finding.api.views.FindingTemplatesViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/finding_templates\.(?P<format>[a-z0-9]+)/?$` | finding_template-list | `dojo.finding.api.views.FindingTemplatesViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/finding_templates/(?P<pk>[^/.]+)/$` | finding_template-detail | `dojo.finding.api.views.FindingTemplatesViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/finding_templates/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | finding_template-detail | `dojo.finding.api.views.FindingTemplatesViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/finding_templates/(?P<pk>[^/.]+)/delete_preview/$` | finding_template-delete-preview | `dojo.finding.api.views.FindingTemplatesViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/finding_templates/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | finding_template-delete-preview | `dojo.finding.api.views.FindingTemplatesViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/$` | finding-list | `dojo.finding.api.views.FindingViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings\.(?P<format>[a-z0-9]+)/?$` | finding-list | `dojo.finding.api.views.FindingViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/accept_risks/$` | finding-accept-risks | `dojo.finding.api.views.FindingViewSet` | POST accept_risks | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/accept_risks\.(?P<format>[a-z0-9]+)/?$` | finding-accept-risks | `dojo.finding.api.views.FindingViewSet` | POST accept_risks | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/generate_report/$` | finding-generate-report | `dojo.finding.api.views.FindingViewSet` | POST generate_report | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/generate_report\.(?P<format>[a-z0-9]+)/?$` | finding-generate-report | `dojo.finding.api.views.FindingViewSet` | POST generate_report | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/$` | finding-detail | `dojo.finding.api.views.FindingViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | finding-detail | `dojo.finding.api.views.FindingViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/close/$` | finding-close | `dojo.finding.api.views.FindingViewSet` | POST close | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/close\.(?P<format>[a-z0-9]+)/?$` | finding-close | `dojo.finding.api.views.FindingViewSet` | POST close | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/delete_preview/$` | finding-delete-preview | `dojo.finding.api.views.FindingViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | finding-delete-preview | `dojo.finding.api.views.FindingViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/files/download/(?P<file_id>\d+)/$` | finding-download-file | `dojo.finding.api.views.FindingViewSet` | GET download_file | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/files/download/(?P<file_id>\d+)\.(?P<format>[a-z0-9]+)/?$` | finding-download-file | `dojo.finding.api.views.FindingViewSet` | GET download_file | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/files/$` | finding-files | `dojo.finding.api.views.FindingViewSet` | GET files, POST files | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/files\.(?P<format>[a-z0-9]+)/?$` | finding-files | `dojo.finding.api.views.FindingViewSet` | GET files, POST files | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/duplicate/$` | finding-get-duplicate-cluster | `dojo.finding.api.views.FindingViewSet` | GET get_duplicate_cluster | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/duplicate\.(?P<format>[a-z0-9]+)/?$` | finding-get-duplicate-cluster | `dojo.finding.api.views.FindingViewSet` | GET get_duplicate_cluster | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/metadata/$` | finding-metadata | `dojo.finding.api.views.FindingViewSet` | POST metadata, PUT metadata, DELETE metadata, GET metadata | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/metadata\.(?P<format>[a-z0-9]+)/?$` | finding-metadata | `dojo.finding.api.views.FindingViewSet` | POST metadata, PUT metadata, DELETE metadata, GET metadata | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/notes/$` | finding-notes | `dojo.finding.api.views.FindingViewSet` | GET notes, POST notes | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/notes\.(?P<format>[a-z0-9]+)/?$` | finding-notes | `dojo.finding.api.views.FindingViewSet` | GET notes, POST notes | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/remove_note/$` | finding-remove-note | `dojo.finding.api.views.FindingViewSet` | PATCH remove_note | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/remove_note\.(?P<format>[a-z0-9]+)/?$` | finding-remove-note | `dojo.finding.api.views.FindingViewSet` | PATCH remove_note | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/remove_tags/$` | finding-remove-tags | `dojo.finding.api.views.FindingViewSet` | PUT remove_tags, PATCH remove_tags | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/remove_tags\.(?P<format>[a-z0-9]+)/?$` | finding-remove-tags | `dojo.finding.api.views.FindingViewSet` | PUT remove_tags, PATCH remove_tags | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/request_response/$` | finding-request-response | `dojo.finding.api.views.FindingViewSet` | GET request_response, POST request_response | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/request_response\.(?P<format>[a-z0-9]+)/?$` | finding-request-response | `dojo.finding.api.views.FindingViewSet` | GET request_response, POST request_response | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/duplicate/reset/$` | finding-reset-finding-duplicate-status | `dojo.finding.api.views.FindingViewSet` | POST reset_finding_duplicate_status | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/duplicate/reset\.(?P<format>[a-z0-9]+)/?$` | finding-reset-finding-duplicate-status | `dojo.finding.api.views.FindingViewSet` | POST reset_finding_duplicate_status | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/original/(?P<new_fid>\d+)/$` | finding-set-finding-as-original | `dojo.finding.api.views.FindingViewSet` | POST set_finding_as_original | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/original/(?P<new_fid>\d+)\.(?P<format>[a-z0-9]+)/?$` | finding-set-finding-as-original | `dojo.finding.api.views.FindingViewSet` | POST set_finding_as_original | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/tags/$` | finding-tags | `dojo.finding.api.views.FindingViewSet` | GET tags, POST tags | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/tags\.(?P<format>[a-z0-9]+)/?$` | finding-tags | `dojo.finding.api.views.FindingViewSet` | GET tags, POST tags | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/verify/$` | finding-verify | `dojo.finding.api.views.FindingViewSet` | POST verify | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/findings/(?P<pk>[^/.]+)/verify\.(?P<format>[a-z0-9]+)/?$` | finding-verify | `dojo.finding.api.views.FindingViewSet` | POST verify | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/request_response_pairs/$` | request_response_pairs-list | `dojo.finding.api.views.BurpRawRequestResponseViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/request_response_pairs\.(?P<format>[a-z0-9]+)/?$` | request_response_pairs-list | `dojo.finding.api.views.BurpRawRequestResponseViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/request_response_pairs/(?P<pk>[^/.]+)/$` | request_response_pairs-detail | `dojo.finding.api.views.BurpRawRequestResponseViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/request_response_pairs/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | request_response_pairs-detail | `dojo.finding.api.views.BurpRawRequestResponseViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/request_response_pairs/(?P<pk>[^/.]+)/delete_preview/$` | request_response_pairs-delete-preview | `dojo.finding.api.views.BurpRawRequestResponseViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/request_response_pairs/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | request_response_pairs-delete-preview | `dojo.finding.api.views.BurpRawRequestResponseViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/regulations/$` | regulations-list | `dojo.regulations.api.views.RegulationsViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/regulations\.(?P<format>[a-z0-9]+)/?$` | regulations-list | `dojo.regulations.api.views.RegulationsViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/regulations/(?P<pk>[^/.]+)/$` | regulations-detail | `dojo.regulations.api.views.RegulationsViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/regulations/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | regulations-detail | `dojo.regulations.api.views.RegulationsViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/regulations/(?P<pk>[^/.]+)/delete_preview/$` | regulations-delete-preview | `dojo.regulations.api.views.RegulationsViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/regulations/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | regulations-delete-preview | `dojo.regulations.api.views.RegulationsViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/reimport-scan/$` | reimportscan-list | `dojo.api_v2.views.ReImportScanView` | POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/reimport-scan\.(?P<format>[a-z0-9]+)/?$` | reimportscan-list | `dojo.api_v2.views.ReImportScanView` | POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/risk_acceptance/$` | risk_acceptance-list | `dojo.risk_acceptance.api.views.RiskAcceptanceViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/risk_acceptance\.(?P<format>[a-z0-9]+)/?$` | risk_acceptance-list | `dojo.risk_acceptance.api.views.RiskAcceptanceViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/risk_acceptance/(?P<pk>[^/.]+)/$` | risk_acceptance-detail | `dojo.risk_acceptance.api.views.RiskAcceptanceViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/risk_acceptance/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | risk_acceptance-detail | `dojo.risk_acceptance.api.views.RiskAcceptanceViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/risk_acceptance/(?P<pk>[^/.]+)/delete_preview/$` | risk_acceptance-delete-preview | `dojo.risk_acceptance.api.views.RiskAcceptanceViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/risk_acceptance/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | risk_acceptance-delete-preview | `dojo.risk_acceptance.api.views.RiskAcceptanceViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/risk_acceptance/(?P<pk>[^/.]+)/download_proof/$` | risk_acceptance-download-proof | `dojo.risk_acceptance.api.views.RiskAcceptanceViewSet` | GET download_proof | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/risk_acceptance/(?P<pk>[^/.]+)/download_proof\.(?P<format>[a-z0-9]+)/?$` | risk_acceptance-download-proof | `dojo.risk_acceptance.api.views.RiskAcceptanceViewSet` | GET download_proof | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/risk_acceptance/(?P<pk>[^/.]+)/expire/$` | risk_acceptance-expire | `dojo.risk_acceptance.api.views.RiskAcceptanceViewSet` | POST expire | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/risk_acceptance/(?P<pk>[^/.]+)/expire\.(?P<format>[a-z0-9]+)/?$` | risk_acceptance-expire | `dojo.risk_acceptance.api.views.RiskAcceptanceViewSet` | POST expire | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/risk_acceptance/(?P<pk>[^/.]+)/notes/$` | risk_acceptance-notes | `dojo.risk_acceptance.api.views.RiskAcceptanceViewSet` | GET notes, POST notes | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/risk_acceptance/(?P<pk>[^/.]+)/notes\.(?P<format>[a-z0-9]+)/?$` | risk_acceptance-notes | `dojo.risk_acceptance.api.views.RiskAcceptanceViewSet` | GET notes, POST notes | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/risk_acceptance/(?P<pk>[^/.]+)/reinstate/$` | risk_acceptance-reinstate | `dojo.risk_acceptance.api.views.RiskAcceptanceViewSet` | POST reinstate | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/risk_acceptance/(?P<pk>[^/.]+)/reinstate\.(?P<format>[a-z0-9]+)/?$` | risk_acceptance-reinstate | `dojo.risk_acceptance.api.views.RiskAcceptanceViewSet` | POST reinstate | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sla_configurations/$` | sla_configurations-list | `dojo.api_v2.views.SLAConfigurationViewset` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sla_configurations\.(?P<format>[a-z0-9]+)/?$` | sla_configurations-list | `dojo.api_v2.views.SLAConfigurationViewset` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sla_configurations/(?P<pk>[^/.]+)/$` | sla_configurations-detail | `dojo.api_v2.views.SLAConfigurationViewset` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sla_configurations/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | sla_configurations-detail | `dojo.api_v2.views.SLAConfigurationViewset` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sla_configurations/(?P<pk>[^/.]+)/delete_preview/$` | sla_configurations-delete-preview | `dojo.api_v2.views.SLAConfigurationViewset` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sla_configurations/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | sla_configurations-delete-preview | `dojo.api_v2.views.SLAConfigurationViewset` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sonarqube_issues/$` | sonarqube_issue-list | `dojo.api_v2.views.SonarqubeIssueViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sonarqube_issues\.(?P<format>[a-z0-9]+)/?$` | sonarqube_issue-list | `dojo.api_v2.views.SonarqubeIssueViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sonarqube_issues/(?P<pk>[^/.]+)/$` | sonarqube_issue-detail | `dojo.api_v2.views.SonarqubeIssueViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sonarqube_issues/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | sonarqube_issue-detail | `dojo.api_v2.views.SonarqubeIssueViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sonarqube_issues/(?P<pk>[^/.]+)/delete_preview/$` | sonarqube_issue-delete-preview | `dojo.api_v2.views.SonarqubeIssueViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sonarqube_issues/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | sonarqube_issue-delete-preview | `dojo.api_v2.views.SonarqubeIssueViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sonarqube_transitions/$` | sonarqube_issue_transition-list | `dojo.api_v2.views.SonarqubeIssueTransitionViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sonarqube_transitions\.(?P<format>[a-z0-9]+)/?$` | sonarqube_issue_transition-list | `dojo.api_v2.views.SonarqubeIssueTransitionViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sonarqube_transitions/(?P<pk>[^/.]+)/$` | sonarqube_issue_transition-detail | `dojo.api_v2.views.SonarqubeIssueTransitionViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sonarqube_transitions/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | sonarqube_issue_transition-detail | `dojo.api_v2.views.SonarqubeIssueTransitionViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sonarqube_transitions/(?P<pk>[^/.]+)/delete_preview/$` | sonarqube_issue_transition-delete-preview | `dojo.api_v2.views.SonarqubeIssueTransitionViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/sonarqube_transitions/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | sonarqube_issue_transition-delete-preview | `dojo.api_v2.views.SonarqubeIssueTransitionViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/system_settings/$` | system_settings-list | `dojo.system_settings.api.views.SystemSettingsViewSet` | GET list | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/system_settings\.(?P<format>[a-z0-9]+)/?$` | system_settings-list | `dojo.system_settings.api.views.SystemSettingsViewSet` | GET list | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/system_settings/(?P<pk>[^/.]+)/$` | system_settings-detail | `dojo.system_settings.api.views.SystemSettingsViewSet` | PUT update, PATCH partial_update | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/system_settings/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | system_settings-detail | `dojo.system_settings.api.views.SystemSettingsViewSet` | PUT update, PATCH partial_update | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/technologies/$` | app_analysis-list | `dojo.api_v2.views.AppAnalysisViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/technologies\.(?P<format>[a-z0-9]+)/?$` | app_analysis-list | `dojo.api_v2.views.AppAnalysisViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/technologies/(?P<pk>[^/.]+)/$` | app_analysis-detail | `dojo.api_v2.views.AppAnalysisViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/technologies/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | app_analysis-detail | `dojo.api_v2.views.AppAnalysisViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/technologies/(?P<pk>[^/.]+)/delete_preview/$` | app_analysis-delete-preview | `dojo.api_v2.views.AppAnalysisViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/technologies/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | app_analysis-delete-preview | `dojo.api_v2.views.AppAnalysisViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tests/$` | test-list | `dojo.test.api.views.TestsViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tests\.(?P<format>[a-z0-9]+)/?$` | test-list | `dojo.test.api.views.TestsViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tests/(?P<pk>[^/.]+)/$` | test-detail | `dojo.test.api.views.TestsViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tests/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | test-detail | `dojo.test.api.views.TestsViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tests/(?P<pk>[^/.]+)/accept_risks/$` | test-accept-risks | `dojo.test.api.views.TestsViewSet` | POST accept_risks | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tests/(?P<pk>[^/.]+)/accept_risks\.(?P<format>[a-z0-9]+)/?$` | test-accept-risks | `dojo.test.api.views.TestsViewSet` | POST accept_risks | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tests/(?P<pk>[^/.]+)/delete_preview/$` | test-delete-preview | `dojo.test.api.views.TestsViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tests/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | test-delete-preview | `dojo.test.api.views.TestsViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tests/(?P<pk>[^/.]+)/files/download/(?P<file_id>\d+)/$` | test-download-file | `dojo.test.api.views.TestsViewSet` | GET download_file | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tests/(?P<pk>[^/.]+)/files/download/(?P<file_id>\d+)\.(?P<format>[a-z0-9]+)/?$` | test-download-file | `dojo.test.api.views.TestsViewSet` | GET download_file | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tests/(?P<pk>[^/.]+)/files/$` | test-files | `dojo.test.api.views.TestsViewSet` | GET files, POST files | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tests/(?P<pk>[^/.]+)/files\.(?P<format>[a-z0-9]+)/?$` | test-files | `dojo.test.api.views.TestsViewSet` | GET files, POST files | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tests/(?P<pk>[^/.]+)/generate_report/$` | test-generate-report | `dojo.test.api.views.TestsViewSet` | POST generate_report | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tests/(?P<pk>[^/.]+)/generate_report\.(?P<format>[a-z0-9]+)/?$` | test-generate-report | `dojo.test.api.views.TestsViewSet` | POST generate_report | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tests/(?P<pk>[^/.]+)/notes/$` | test-notes | `dojo.test.api.views.TestsViewSet` | GET notes, POST notes | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tests/(?P<pk>[^/.]+)/notes\.(?P<format>[a-z0-9]+)/?$` | test-notes | `dojo.test.api.views.TestsViewSet` | GET notes, POST notes | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/test_types/$` | test_type-list | `dojo.test.api.views.TestTypesViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/test_types\.(?P<format>[a-z0-9]+)/?$` | test_type-list | `dojo.test.api.views.TestTypesViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/test_types/(?P<pk>[^/.]+)/$` | test_type-detail | `dojo.test.api.views.TestTypesViewSet` | GET retrieve, PUT update, PATCH partial_update | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/test_types/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | test_type-detail | `dojo.test.api.views.TestTypesViewSet` | GET retrieve, PUT update, PATCH partial_update | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/test_imports/$` | test_imports-list | `dojo.test.api.views.TestImportViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/test_imports\.(?P<format>[a-z0-9]+)/?$` | test_imports-list | `dojo.test.api.views.TestImportViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/test_imports/(?P<pk>[^/.]+)/$` | test_imports-detail | `dojo.test.api.views.TestImportViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/test_imports/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | test_imports-detail | `dojo.test.api.views.TestImportViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/test_imports/(?P<pk>[^/.]+)/delete_preview/$` | test_imports-delete-preview | `dojo.test.api.views.TestImportViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/test_imports/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | test_imports-delete-preview | `dojo.test.api.views.TestImportViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_configurations/$` | tool_configuration-list | `dojo.tool_config.api.views.ToolConfigurationsViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_configurations\.(?P<format>[a-z0-9]+)/?$` | tool_configuration-list | `dojo.tool_config.api.views.ToolConfigurationsViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_configurations/(?P<pk>[^/.]+)/$` | tool_configuration-detail | `dojo.tool_config.api.views.ToolConfigurationsViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_configurations/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | tool_configuration-detail | `dojo.tool_config.api.views.ToolConfigurationsViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_configurations/(?P<pk>[^/.]+)/delete_preview/$` | tool_configuration-delete-preview | `dojo.tool_config.api.views.ToolConfigurationsViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_configurations/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | tool_configuration-delete-preview | `dojo.tool_config.api.views.ToolConfigurationsViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_product_settings/$` | tool_product_settings-list | `dojo.tool_product.api.views.ToolProductSettingsViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_product_settings\.(?P<format>[a-z0-9]+)/?$` | tool_product_settings-list | `dojo.tool_product.api.views.ToolProductSettingsViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_product_settings/(?P<pk>[^/.]+)/$` | tool_product_settings-detail | `dojo.tool_product.api.views.ToolProductSettingsViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_product_settings/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | tool_product_settings-detail | `dojo.tool_product.api.views.ToolProductSettingsViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_product_settings/(?P<pk>[^/.]+)/delete_preview/$` | tool_product_settings-delete-preview | `dojo.tool_product.api.views.ToolProductSettingsViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_product_settings/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | tool_product_settings-delete-preview | `dojo.tool_product.api.views.ToolProductSettingsViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_types/$` | tool_type-list | `dojo.tool_type.api.views.ToolTypesViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_types\.(?P<format>[a-z0-9]+)/?$` | tool_type-list | `dojo.tool_type.api.views.ToolTypesViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_types/(?P<pk>[^/.]+)/$` | tool_type-detail | `dojo.tool_type.api.views.ToolTypesViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_types/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | tool_type-detail | `dojo.tool_type.api.views.ToolTypesViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_types/(?P<pk>[^/.]+)/delete_preview/$` | tool_type-delete-preview | `dojo.tool_type.api.views.ToolTypesViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/tool_types/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | tool_type-delete-preview | `dojo.tool_type.api.views.ToolTypesViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/users/$` | user-list | `dojo.user.api.views.UsersViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/users\.(?P<format>[a-z0-9]+)/?$` | user-list | `dojo.user.api.views.UsersViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/users/(?P<pk>[^/.]+)/$` | user-detail | `dojo.user.api.views.UsersViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/users/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | user-detail | `dojo.user.api.views.UsersViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/users/(?P<pk>[^/.]+)/delete_preview/$` | user-delete-preview | `dojo.user.api.views.UsersViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/users/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | user-delete-preview | `dojo.user.api.views.UsersViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/users/(?P<pk>[^/.]+)/reset_api_token/$` | user-reset-api-token | `dojo.user.api.views.UsersViewSet` | POST reset_api_token | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/users/(?P<pk>[^/.]+)/reset_api_token\.(?P<format>[a-z0-9]+)/?$` | user-reset-api-token | `dojo.user.api.views.UsersViewSet` | POST reset_api_token | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/user_contact_infos/$` | usercontactinfo-list | `dojo.user.api.views.UserContactInfoViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/user_contact_infos\.(?P<format>[a-z0-9]+)/?$` | usercontactinfo-list | `dojo.user.api.views.UserContactInfoViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/user_contact_infos/(?P<pk>[^/.]+)/$` | usercontactinfo-detail | `dojo.user.api.views.UserContactInfoViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/user_contact_infos/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | usercontactinfo-detail | `dojo.user.api.views.UserContactInfoViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/user_contact_infos/(?P<pk>[^/.]+)/delete_preview/$` | usercontactinfo-delete-preview | `dojo.user.api.views.UserContactInfoViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/user_contact_infos/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | usercontactinfo-delete-preview | `dojo.user.api.views.UserContactInfoViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/repositories/$` | repository-list | `dojo.scm.api.views.RepositoryViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/repositories\.(?P<format>[a-z0-9]+)/?$` | repository-list | `dojo.scm.api.views.RepositoryViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/repositories/(?P<pk>[^/.]+)/$` | repository-detail | `dojo.scm.api.views.RepositoryViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/repositories/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | repository-detail | `dojo.scm.api.views.RepositoryViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/repositories/(?P<pk>[^/.]+)/delete_preview/$` | repository-delete-preview | `dojo.scm.api.views.RepositoryViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/repositories/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | repository-delete-preview | `dojo.scm.api.views.RepositoryViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/commits/$` | commit-list | `dojo.scm.api.views.CommitViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/commits\.(?P<format>[a-z0-9]+)/?$` | commit-list | `dojo.scm.api.views.CommitViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/commits/(?P<pk>[^/.]+)/$` | commit-detail | `dojo.scm.api.views.CommitViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/commits/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | commit-detail | `dojo.scm.api.views.CommitViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/commits/(?P<pk>[^/.]+)/delete_preview/$` | commit-delete-preview | `dojo.scm.api.views.CommitViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/commits/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | commit-delete-preview | `dojo.scm.api.views.CommitViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/location/$` | location-list | `dojo.location.api.views.LocationViewSet` | GET list | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/location\.(?P<format>[a-z0-9]+)/?$` | location-list | `dojo.location.api.views.LocationViewSet` | GET list | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/location/(?P<pk>[^/.]+)/$` | location-detail | `dojo.location.api.views.LocationViewSet` | GET retrieve | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/location/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | location-detail | `dojo.location.api.views.LocationViewSet` | GET retrieve | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/location_findings/$` | location_findings-list | `dojo.location.api.views.LocationFindingReferenceViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/location_findings\.(?P<format>[a-z0-9]+)/?$` | location_findings-list | `dojo.location.api.views.LocationFindingReferenceViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/location_findings/(?P<pk>[^/.]+)/$` | location_findings-detail | `dojo.location.api.views.LocationFindingReferenceViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/location_findings/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | location_findings-detail | `dojo.location.api.views.LocationFindingReferenceViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/location_findings/(?P<pk>[^/.]+)/delete_preview/$` | location_findings-delete-preview | `dojo.location.api.views.LocationFindingReferenceViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/location_findings/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | location_findings-delete-preview | `dojo.location.api.views.LocationFindingReferenceViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/location_products/$` | location_products-list | `dojo.location.api.views.LocationProductReferenceViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/location_products\.(?P<format>[a-z0-9]+)/?$` | location_products-list | `dojo.location.api.views.LocationProductReferenceViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/location_products/(?P<pk>[^/.]+)/$` | location_products-detail | `dojo.location.api.views.LocationProductReferenceViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/location_products/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | location_products-detail | `dojo.location.api.views.LocationProductReferenceViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/location_products/(?P<pk>[^/.]+)/delete_preview/$` | location_products-delete-preview | `dojo.location.api.views.LocationProductReferenceViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/location_products/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | location_products-delete-preview | `dojo.location.api.views.LocationProductReferenceViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/url/$` | url-list | `dojo.url.api.views.URLViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/url\.(?P<format>[a-z0-9]+)/?$` | url-list | `dojo.url.api.views.URLViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/url/(?P<pk>[^/.]+)/$` | url-detail | `dojo.url.api.views.URLViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/url/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | url-detail | `dojo.url.api.views.URLViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/url/(?P<pk>[^/.]+)/delete_preview/$` | url-delete-preview | `dojo.url.api.views.URLViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/url/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | url-delete-preview | `dojo.url.api.views.URLViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/endpoints/$` | endpoint-list | `dojo.location.api.endpoint_compat.V3EndpointCompatibleViewSet` | GET list | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/endpoints\.(?P<format>[a-z0-9]+)/?$` | endpoint-list | `dojo.location.api.endpoint_compat.V3EndpointCompatibleViewSet` | GET list | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/endpoints/(?P<pk>[^/.]+)/$` | endpoint-detail | `dojo.location.api.endpoint_compat.V3EndpointCompatibleViewSet` | GET retrieve | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/endpoints/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | endpoint-detail | `dojo.location.api.endpoint_compat.V3EndpointCompatibleViewSet` | GET retrieve | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/endpoints/(?P<pk>[^/.]+)/generate_report/$` | endpoint-generate-report | `dojo.location.api.endpoint_compat.V3EndpointCompatibleViewSet` | POST generate_report | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/endpoints/(?P<pk>[^/.]+)/generate_report\.(?P<format>[a-z0-9]+)/?$` | endpoint-generate-report | `dojo.location.api.endpoint_compat.V3EndpointCompatibleViewSet` | POST generate_report | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/endpoint_status/$` | endpoint_status-list | `dojo.location.api.endpoint_compat.V3EndpointStatusCompatibleViewSet` | GET list | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/endpoint_status\.(?P<format>[a-z0-9]+)/?$` | endpoint_status-list | `dojo.location.api.endpoint_compat.V3EndpointStatusCompatibleViewSet` | GET list | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/endpoint_status/(?P<pk>[^/.]+)/$` | endpoint_status-detail | `dojo.location.api.endpoint_compat.V3EndpointStatusCompatibleViewSet` | GET retrieve | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/endpoint_status/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | endpoint_status-detail | `dojo.location.api.endpoint_compat.V3EndpointStatusCompatibleViewSet` | GET retrieve | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/celery/queue/details/$` | celery-queue-details | `dojo.api_v2.views.CeleryViewSet` | GET queue_details | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/celery/queue/details\.(?P<format>[a-z0-9]+)/?$` | celery-queue-details | `dojo.api_v2.views.CeleryViewSet` | GET queue_details | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/celery/queue/purge/$` | celery-queue-purge | `dojo.api_v2.views.CeleryViewSet` | POST queue_purge | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/celery/queue/purge\.(?P<format>[a-z0-9]+)/?$` | celery-queue-purge | `dojo.api_v2.views.CeleryViewSet` | POST queue_purge | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/celery/queue/task/purge/$` | celery-queue-task-purge | `dojo.api_v2.views.CeleryViewSet` | POST queue_task_purge | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/celery/queue/task/purge\.(?P<format>[a-z0-9]+)/?$` | celery-queue-task-purge | `dojo.api_v2.views.CeleryViewSet` | POST queue_task_purge | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/celery/status/$` | celery-status | `dojo.api_v2.views.CeleryViewSet` | GET status | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/celery/status\.(?P<format>[a-z0-9]+)/?$` | celery-status | `dojo.api_v2.views.CeleryViewSet` | GET status | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/assets/$` | asset-list | `dojo.asset.api.views.AssetViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/assets\.(?P<format>[a-z0-9]+)/?$` | asset-list | `dojo.asset.api.views.AssetViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/assets/(?P<pk>[^/.]+)/$` | asset-detail | `dojo.asset.api.views.AssetViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/assets/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | asset-detail | `dojo.asset.api.views.AssetViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/assets/(?P<pk>[^/.]+)/delete_preview/$` | asset-delete-preview | `dojo.asset.api.views.AssetViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/assets/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | asset-delete-preview | `dojo.asset.api.views.AssetViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/assets/(?P<pk>[^/.]+)/generate_report/$` | asset-generate-report | `dojo.asset.api.views.AssetViewSet` | POST generate_report | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/assets/(?P<pk>[^/.]+)/generate_report\.(?P<format>[a-z0-9]+)/?$` | asset-generate-report | `dojo.asset.api.views.AssetViewSet` | POST generate_report | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/asset_api_scan_configurations/$` | asset_api_scan_configuration-list | `dojo.asset.api.views.AssetAPIScanConfigurationViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/asset_api_scan_configurations\.(?P<format>[a-z0-9]+)/?$` | asset_api_scan_configuration-list | `dojo.asset.api.views.AssetAPIScanConfigurationViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/asset_api_scan_configurations/(?P<pk>[^/.]+)/$` | asset_api_scan_configuration-detail | `dojo.asset.api.views.AssetAPIScanConfigurationViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/asset_api_scan_configurations/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | asset_api_scan_configuration-detail | `dojo.asset.api.views.AssetAPIScanConfigurationViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/asset_api_scan_configurations/(?P<pk>[^/.]+)/delete_preview/$` | asset_api_scan_configuration-delete-preview | `dojo.asset.api.views.AssetAPIScanConfigurationViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/asset_api_scan_configurations/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | asset_api_scan_configuration-delete-preview | `dojo.asset.api.views.AssetAPIScanConfigurationViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/cicd_infrastructure/$` | cicd_infrastructure-list | `dojo.cicd_infrastructure.api.views.CICDInfrastructureViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/cicd_infrastructure\.(?P<format>[a-z0-9]+)/?$` | cicd_infrastructure-list | `dojo.cicd_infrastructure.api.views.CICDInfrastructureViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/cicd_infrastructure/(?P<pk>[^/.]+)/$` | cicd_infrastructure-detail | `dojo.cicd_infrastructure.api.views.CICDInfrastructureViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/cicd_infrastructure/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | cicd_infrastructure-detail | `dojo.cicd_infrastructure.api.views.CICDInfrastructureViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/cicd_infrastructure/(?P<pk>[^/.]+)/delete_preview/$` | cicd_infrastructure-delete-preview | `dojo.cicd_infrastructure.api.views.CICDInfrastructureViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/cicd_infrastructure/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | cicd_infrastructure-delete-preview | `dojo.cicd_infrastructure.api.views.CICDInfrastructureViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/organizations/$` | organization-list | `dojo.organization.api.views.OrganizationViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/organizations\.(?P<format>[a-z0-9]+)/?$` | organization-list | `dojo.organization.api.views.OrganizationViewSet` | GET list, POST create | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/organizations/(?P<pk>[^/.]+)/$` | organization-detail | `dojo.organization.api.views.OrganizationViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/organizations/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$` | organization-detail | `dojo.organization.api.views.OrganizationViewSet` | GET retrieve, PUT update, PATCH partial_update, DELETE destroy | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/organizations/(?P<pk>[^/.]+)/delete_preview/$` | organization-delete-preview | `dojo.organization.api.views.OrganizationViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/organizations/(?P<pk>[^/.]+)/delete_preview\.(?P<format>[a-z0-9]+)/?$` | organization-delete-preview | `dojo.organization.api.views.OrganizationViewSet` | GET delete_preview | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/organizations/(?P<pk>[^/.]+)/generate_report/$` | organization-generate-report | `dojo.organization.api.views.OrganizationViewSet` | POST generate_report | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/organizations/(?P<pk>[^/.]+)/generate_report\.(?P<format>[a-z0-9]+)/?$` | organization-generate-report | `dojo.organization.api.views.OrganizationViewSet` | POST generate_report | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/` | api-root | `rest_framework.routers.APIRootView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/<drf_format_suffix:format>` | api-root | `rest_framework.routers.APIRootView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/user_profile/` | user_profile | `dojo.user.api.views.UserProfileView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/api-tokens/revoke/$` | api-token-revoke | `dojo.user.api.views.RevokeApiTokenView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/export/manifest/$` | export-manifest | `dojo.export.api.views.ExportManifestView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/export/products/(?P<pk>[0-9]+)/$` | export-product | `dojo.export.api.views.ProductExportView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v2/api-token-auth/` | api-token-auth | `dojo.user.api.views.ForcedResetObtainAuthToken` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/reference$` | api_v3_reference | `dojo.api_v3.reference_docs.scalar_reference` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/openapi.json` | api_v3:openapi-json | `functools.partial` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/docs` | api_v3:openapi-view | `functools.partial` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings` | api_v3:findings_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings` | api_v3:findings_create | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings/export.csv` | api_v3:findings_export_csv | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings/<int:finding_id>` | api_v3:findings_detail | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings/<int:finding_id>` | api_v3:findings_update | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings/<int:finding_id>` | api_v3:findings_replace | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings/<int:finding_id>` | api_v3:findings_delete | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/organizations` | api_v3:organizations_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/organizations` | api_v3:organizations_create | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/organizations/export.csv` | api_v3:organizations_export_csv | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/organizations/<int:organization_id>` | api_v3:organizations_detail | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/organizations/<int:organization_id>` | api_v3:organizations_update | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/organizations/<int:organization_id>` | api_v3:organizations_replace | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/organizations/<int:organization_id>` | api_v3:organizations_delete | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/assets` | api_v3:assets_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/assets` | api_v3:assets_create | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/assets/export.csv` | api_v3:assets_export_csv | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/assets/<int:asset_id>` | api_v3:assets_detail | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/assets/<int:asset_id>` | api_v3:assets_update | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/assets/<int:asset_id>` | api_v3:assets_replace | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/assets/<int:asset_id>` | api_v3:assets_delete | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/engagements` | api_v3:engagements_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/engagements` | api_v3:engagements_create | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/engagements/export.csv` | api_v3:engagements_export_csv | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/engagements/<int:engagement_id>` | api_v3:engagements_detail | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/engagements/<int:engagement_id>` | api_v3:engagements_update | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/engagements/<int:engagement_id>` | api_v3:engagements_replace | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/engagements/<int:engagement_id>` | api_v3:engagements_delete | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/tests` | api_v3:tests_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/tests` | api_v3:tests_create | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/tests/export.csv` | api_v3:tests_export_csv | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/tests/<int:test_id>` | api_v3:tests_detail | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/tests/<int:test_id>` | api_v3:tests_update | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/tests/<int:test_id>` | api_v3:tests_replace | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/tests/<int:test_id>` | api_v3:tests_delete | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/users` | api_v3:users_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/users` | api_v3:users_create | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/users/export.csv` | api_v3:users_export_csv | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/users/<int:user_id>` | api_v3:users_detail | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/users/<int:user_id>` | api_v3:users_update | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/users/<int:user_id>` | api_v3:users_replace | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/users/<int:user_id>` | api_v3:users_delete | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/locations` | api_v3:locations_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/locations/export.csv` | api_v3:locations_export_csv | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/locations/<int:location_id>` | api_v3:locations_detail | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings/<int:finding_id>/locations` | api_v3:finding_locations_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/assets/<int:asset_id>/locations` | api_v3:asset_locations_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/import` | api_v3:import | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings/<int:parent_id>/notes` | api_v3:findings_notes_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings/<int:parent_id>/notes` | api_v3:findings_notes_create | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings/<int:parent_id>/files` | api_v3:findings_files_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings/<int:parent_id>/files` | api_v3:findings_files_create | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings/<int:parent_id>/files/<int:file_id>/download` | api_v3:findings_files_download | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/engagements/<int:parent_id>/notes` | api_v3:engagements_notes_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/engagements/<int:parent_id>/notes` | api_v3:engagements_notes_create | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/engagements/<int:parent_id>/files` | api_v3:engagements_files_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/engagements/<int:parent_id>/files` | api_v3:engagements_files_create | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/engagements/<int:parent_id>/files/<int:file_id>/download` | api_v3:engagements_files_download | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/tests/<int:parent_id>/notes` | api_v3:tests_notes_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/tests/<int:parent_id>/notes` | api_v3:tests_notes_create | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/tests/<int:parent_id>/files` | api_v3:tests_files_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/tests/<int:parent_id>/files` | api_v3:tests_files_create | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/tests/<int:parent_id>/files/<int:file_id>/download` | api_v3:tests_files_download | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings/<int:parent_id>/tags` | api_v3:findings_tags_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings/<int:parent_id>/tags` | api_v3:findings_tags_replace | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings/<int:parent_id>/tags` | api_v3:findings_tags_append | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/findings/<int:parent_id>/tags/<tag>` | api_v3:findings_tags_delete | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/engagements/<int:parent_id>/tags` | api_v3:engagements_tags_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/engagements/<int:parent_id>/tags` | api_v3:engagements_tags_replace | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/engagements/<int:parent_id>/tags` | api_v3:engagements_tags_append | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/engagements/<int:parent_id>/tags/<tag>` | api_v3:engagements_tags_delete | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/tests/<int:parent_id>/tags` | api_v3:tests_tags_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/tests/<int:parent_id>/tags` | api_v3:tests_tags_replace | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/tests/<int:parent_id>/tags` | api_v3:tests_tags_append | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/tests/<int:parent_id>/tags/<tag>` | api_v3:tests_tags_delete | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/assets/<int:parent_id>/tags` | api_v3:assets_tags_list | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/assets/<int:parent_id>/tags` | api_v3:assets_tags_replace | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/assets/<int:parent_id>/tags` | api_v3:assets_tags_append | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/assets/<int:parent_id>/tags/<tag>` | api_v3:assets_tags_delete | `ninja.operation.PathView.get_view.<locals>.sync_view_wrapper` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/api/v3/` | api_v3:api-root | `functools.partial` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/questionnaire$` | questionnaire | `dojo.survey.ui.views.questionnaire` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/questionnaire/create$` | create_questionnaire | `dojo.survey.ui.views.create_questionnaire` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/questionnaire/(?P<sid>\d+)/edit$` | edit_questionnaire | `dojo.survey.ui.views.edit_questionnaire` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/questionnaire/(?P<sid>\d+)/delete` | delete_questionnaire | `dojo.survey.ui.views.delete_questionnaire` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/questionnaire/(?P<sid>\d+)/edit/questions$` | edit_questionnaire_questions | `dojo.survey.ui.views.edit_questionnaire_questions` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/questions$` | questions | `dojo.survey.ui.views.questions` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/questions/add$` | create_question | `dojo.survey.ui.views.create_question` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/questions/(?P<qid>\d+)/edit$` | edit_question | `dojo.survey.ui.views.edit_question` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/choices/add$` | add_choices | `dojo.survey.ui.views.add_choices` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/add_questionnaire$` | add_questionnaire | `dojo.survey.ui.views.add_questionnaire` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/questionnaire/(?P<sid>\d+)/answer` | answer_questionnaire | `dojo.survey.ui.views.answer_questionnaire` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/questionnaire/(?P<sid>\d+)/delete` | delete_engagement_survey | `dojo.survey.ui.views.delete_engagement_survey` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/questionnaire/(?P<sid>\d+)$` | view_questionnaire | `dojo.survey.ui.views.view_questionnaire` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/engagement/(?P<eid>\d+)/questionnaire/(?P<sid>\d+)/assign` | assign_questionnaire | `dojo.survey.ui.views.assign_questionnaire` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/empty_questionnaire$` | add_empty_questionnaire | `dojo.survey.ui.views.add_empty_questionnaire` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/empty_questionnaire/(?P<esid>\d+)$` | view_empty_survey | `dojo.survey.ui.views.view_empty_survey` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/empty_questionnaire/(?P<esid>\d+)/delete$` | delete_empty_questionnaire | `dojo.survey.ui.views.delete_empty_questionnaire` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/general_questionnaire/(?P<esid>\d+)/delete$` | delete_general_questionnaire | `dojo.survey.ui.views.delete_general_questionnaire` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/empty_questionnaire/(?P<esid>\d+)/answer$` | answer_empty_survey | `dojo.survey.ui.views.answer_empty_survey` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/empty_questionnaire/(?P<esid>\d+)/new_engagement$` | engagement_empty_survey | `dojo.survey.ui.views.engagement_empty_survey` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
| `/empty_questionnaire/(?P<esid>\d+)/existing_engagement$` | existing_engagement_empty_survey | `dojo.survey.ui.views.ExistingEngagementEmptySurveyView` | — | — | — | Запись resolver | NOT TESTED · route-inventory.json |
