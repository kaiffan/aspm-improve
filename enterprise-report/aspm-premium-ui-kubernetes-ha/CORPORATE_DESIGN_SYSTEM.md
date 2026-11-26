# Дизайн-система ASPM

Сохранены базовые цвета ASPM #c1ff05, #9e6fc3 и #ff7d32. Общая шкала CSS-переменных задаёт primary, secondary, accent, фон, поверхность, текст, границу, фокус, состояния, severity, типографику, плотность таблиц, размер контролов, скругления и тени. Деление по цвету дублируется текстом статуса. Light, Dark и System доступны в шапке и на входе.

| Область | Переменные |
| --- | --- |
| Идентичность | DD_ASPM_BRAND_NAME, DD_ASPM_BRAND_MARK, DD_ASPM_FAVICON |
| Акценты | DD_ASPM_BRAND_PRIMARY, DD_ASPM_BRAND_SECONDARY, DD_ASPM_BRAND_ACCENT |
| Поверхность и панель | DD_ASPM_BRAND_LIGHT_SURFACE, DD_ASPM_BRAND_DARK_SURFACE, DD_ASPM_BRAND_LIGHT_SIDEBAR, DD_ASPM_BRAND_DARK_SIDEBAR |

Доступны шестизначные HEX и локальные пути для логотипа и favicon. Для брендированных фонов вычисляется белый или чёрный цвет текста. Варианты корпоративной палитры требуют собственного теста контраста ссылок, границ и активных состояний.
