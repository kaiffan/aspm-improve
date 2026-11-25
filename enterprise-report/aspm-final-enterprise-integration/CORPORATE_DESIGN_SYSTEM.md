# Corporate design system

ASPM extends its existing light, dark and system themes in `dojo/static/dojo/css/aspm.css`. The stylesheet carries primary, secondary, accent, ground, surface, border, semantic status and severity colors, typography, radius and responsive table padding. The new portfolio, policy, mapping and integration pages use the same components.

Use a relative static asset path in `DD_ASPM_BRAND_MARK` and `DD_ASPM_FAVICON` and configure `DD_ASPM_BRAND_NAME` to change branding. Optional primary, secondary and accent environment overrides accept six-digit HEX only. Foreground contrast for a custom primary is derived when rendering. The default palette remains the source product's palette.

Use keyboard-operable native forms and buttons. Status text stays visible independently of severity color. Long tables scroll within their section. The browser lab records desktop, tablet and mobile layouts. A comprehensive WCAG 2.2 AA audit is a separate release gate.
