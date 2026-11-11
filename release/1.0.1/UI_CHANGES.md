# Интерфейс ASPM

Общая система tokens в `dojo/static/dojo/css/aspm.css` расширяет существующий Tailwind/legacy UI. Сохранены Django templates, Alpine, Chart.js, Chosen/Select2 и текущие ORM/form/API обработчики. Нового UI framework нет.

Палитра сверена с [официальной страницей OTP](https://www.otpbank.ru/about/press-centr/logos/): лайм #C1FF05, фиолетовый #9E6FC3, оранжевый #FF7D32, металл #BAB8BA, белый и графит. **Голубой фирменный акцент исключён по запросу пользователя.** Текстовые/фокусные оттенки производные для контраста. Существующая семантика severity сохранена. Используется собственный SVG-щит ASPM, не логотип банка.

Единые карточки, компактные таблицы, формы, фильтры, pagination, dropdown, alerts, вкладки, code/editor, report builder и login. Dashboard получил ясную иерархию и разделители тысяч. Общий shell применяется к finding/product/engagement/test list/detail и основным формам; бизнес-логика Engagements не менялась.

Light/Dark/System сохраняются в localStorage `aspm.theme`. Theme bootstrap загружается синхронно в head до стилей, применяет системную тему без ожидания DOM. Явный выбор имеет приоритет, системный режим реагирует на смену OS, вкладки синхронизируются, отказ storage не ломает интерфейс. Графики меняют только цвета осей/легенд/tooltip; данные/сортировка не меняются.

Мобильная навигация: закрытая панель исключена из tab-порядка, открытая удерживает focus; Escape закрывает и возвращает focus. Есть skip link и видимая focus-рамка. Исправлены скрытая таблица Dashboard, перенос toolbar Test, подписи действий/вкладок, checkbox вне кнопки и асинхронные labels Tagulous. Автоматический axe — дополнительная проверка, не сертификат WCAG.

Убраны Pro purchase/upgrade-пункты, PAYG и удалённый promotional banner/star prompt по умолчанию. Рабочие OSS-функции не активируются/не отключаются ради рекламы. Read-only, security и operator banners сохранены; LICENSE.md/NOTICE и upstream attribution остаются. Support содержит локальную версию, документацию/API и ссылку на форк.

Скриншоты в `screenshots/`: 1440×1000 desktop и 390×844 mobile, обе темы, detail/list/forms/reports/support/login. Префиксы baseline-* — замороженный Round 5 с корректным static gateway. diagnostic-api-only-* — обнаруженная старая API-only конфигурация без static; она исключена из визуального сравнения.

По разделам: Dashboard — новая иерархия/стат-карточки/графики; Findings — плотные list/detail/filter/action controls; Products — согласованные overview/tabs/count displays; Engagements — только общие стили существующих страниц; Tests — responsive toolbar/details/notes/files/actions; Reports — themed builder и собственный print cover/footer metadata; формы — доступные labels, editors, severity/selection; Login — локальная карточка бренда и отдельный theme control. Бизнес-обработчики не переписывались.
