# Интерфейс Classic Workspace

В общем sidebar есть два прямых входа. Classic Workspace показывает Products, их Product Types и короткий путь к Engagements, Metrics и отчётам. У пользователей с рабочими правами также доступны классические списки, формы и Report Builder. DevSecOps Workspace открывает Projects и переходы в Repositories.

Классические страницы используют общий layout, панели, таблицы, элементы форм, типографику и индикаторы Severity. Выбранный режим Light, Dark или System применяется в обоих пространствах. Для USER вложенные страницы показывают разрешённые данные Product и ссылки на отчёты. Классический Test без Git отображается в той же навигации.

| Экран | Браузерное свидетельство |
| --- | --- |
| Classic Workspace, EXPERT, 1440 px | [Скриншот](dual-raw/classic-expert-desktop.png) |
| Нативный Classic Engagement, 1440 px | [Скриншот](dual-raw/classic-engagement-desktop.png) |
| Нативный Classic Test без Git, 1440 px | [Скриншот](dual-raw/classic-test-desktop.png) |
| Classic Workspace, USER, System/Dark, 390 px | [Скриншот](dual-raw/classic-reader-mobile-dark.png) |
| DevSecOps Workspace, EXPERT, 1440 px | [Скриншот](dual-raw/devsecops-expert-desktop.png) |
| DevSecOps Scanner Reports, USER, System/Dark, 390 px | [Скриншот](dual-raw/devsecops-reader-mobile-dark.png) |

При проверке Chromium измерял ширину документа на 1440 и 390 px, подтвердил доступность обоих направлений навигации и возврат к точному ScanRun через связанную страницу Test. Закладка `/product` после входа открывает тот же список разрешённых Products. При смене пространства breadcrumb обновляется. [Результаты браузера](dual-raw/browser.json)

После входа через Keycloak проверены штатные формы создания Product Type, создания и правки Engagement/Test и добавления Finding. Прямой запрос формы импорта скана вернул 404, а попытка USER открыть правку Test вернула 403. [Проверка форм](dual-raw/classic-forms.json)
