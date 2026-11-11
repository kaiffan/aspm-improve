/* Apply before styles/first paint. Storage failure falls back to the system theme. */
(function () {
    'use strict';
    var key = 'aspm.theme', root = document.documentElement;
    var system = window.matchMedia('(prefers-color-scheme: dark)');
    var preference = 'system';
    function valid(value) { return ['light', 'dark', 'system'].indexOf(value) !== -1; }
    try { var saved = localStorage.getItem(key); if (valid(saved)) preference = saved; } catch (_) { /* Private/disabled storage. */ }
    function token(name, fallback) { return getComputedStyle(root).getPropertyValue(name).trim() || fallback; }
    function styleOptions(options) {
        options = options || {};
        var text = token('--color-text-muted', '#536171'), border = token('--color-border', '#e0e4ea');
        if (!options.plugins) options.plugins = {};
        if (options.plugins.legend !== false) {
            if (!options.plugins.legend) options.plugins.legend = {};
            if (!options.plugins.legend.labels) options.plugins.legend.labels = {};
            options.plugins.legend.labels.color = text;
        }
        if (options.plugins.title) options.plugins.title.color = token('--color-text', '#202630');
        if (options.plugins.tooltip !== false) {
            if (!options.plugins.tooltip) options.plugins.tooltip = {};
            Object.assign(options.plugins.tooltip, {backgroundColor: token('--color-surface-2', '#f7f8fa'), titleColor: text, bodyColor: text, footerColor: text, borderColor: border, borderWidth: 1});
        }
        Object.keys(options.scales || {}).forEach(function (key) {
            var axis = options.scales[key];
            if (!axis || typeof axis !== 'object') return;
            if (!axis.ticks) axis.ticks = {}; axis.ticks.color = text;
            if (axis.grid !== false) { if (!axis.grid) axis.grid = {}; axis.grid.color = border; }
            if (axis.border !== false) { if (!axis.border) axis.border = {}; axis.border.color = border; }
            if (axis.title) axis.title.color = text;
            if (axis.pointLabels) axis.pointLabels.color = text;
            if (axis.angleLines) axis.angleLines.color = border;
        });
        return options;
    }
    function updateCharts() {
        if (!window.Chart) return;
        window.Chart.defaults.color = token('--color-text-muted', '#536171');
        window.Chart.defaults.borderColor = token('--color-border', '#e0e4ea');
        Object.values(window.Chart.instances || {}).forEach(function (chart) {
            styleOptions(chart.options);
            if (['pie', 'doughnut'].indexOf(chart.config.type) !== -1) {
                chart.data.datasets.forEach(function (dataset) { dataset.borderColor = token('--color-surface', '#fff'); });
            }
            chart.update('none');
        });
    }
    function apply() {
        var theme = preference === 'system' ? (system.matches ? 'dark' : 'light') : preference;
        root.dataset.theme = theme; root.dataset.themePreference = preference;
        root.style.colorScheme = theme;
        document.querySelectorAll('[data-theme-control]').forEach(function (select) { select.value = preference; });
        window.dispatchEvent(new CustomEvent('aspm:themechange', {detail: {theme: theme, preference: preference}}));
    }
    window.ASPMTheme = {get: function () { return preference; }, set: function (value) {
        if (!valid(value)) return;
        preference = value;
        try { localStorage.setItem(key, value); } catch (_) { /* Keep current tab usable. */ }
        apply();
    }, styleChartOptions: styleOptions};
    apply();
    system.addEventListener('change', function () { if (preference === 'system') apply(); });
    window.addEventListener('storage', function (event) {
        if (event.key === key) { preference = valid(event.newValue) ? event.newValue : 'system'; apply(); }
    });
    window.addEventListener('aspm:themechange', updateCharts);
    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('[data-theme-control]').forEach(function (select) {
            select.value = preference;
            select.addEventListener('change', function () { window.ASPMTheme.set(select.value); });
        });
        updateCharts();
    });
})();

/* ASPM shell: accessible mobile navigation; no network requests or dependencies. */
(function () {
    'use strict';
    document.addEventListener('DOMContentLoaded', function () {
        document.addEventListener('keydown', function (event) {
            if ((event.key === 'Enter' || event.key === ' ') && event.target.matches('#select_by_severity a[role=button]')) { event.preventDefault(); event.target.click(); }
        });
        var root = document.documentElement;
        var sidebar = document.getElementById('dd-sidebar');
        var toggle = document.getElementById('aspm-nav-toggle');
        var backdrop = document.getElementById('aspm-nav-backdrop');
        if (!sidebar || !toggle || !backdrop) return;
        function close(restoreFocus) {
            root.removeAttribute('data-nav-open');
            toggle.setAttribute('aria-expanded', 'false');
            backdrop.hidden = true;
            if (restoreFocus) toggle.focus();
        }
        function focusable() {
            return Array.from(sidebar.querySelectorAll('a[href], button, select, [tabindex="0"]')).filter(function (el) { return el.getClientRects().length && !el.disabled; });
        }
        toggle.addEventListener('click', function () {
            if (root.hasAttribute('data-nav-open')) return close(true);
            root.setAttribute('data-nav-open', '');
            toggle.setAttribute('aria-expanded', 'true');
            backdrop.hidden = false;
            requestAnimationFrame(function () { var first = focusable()[0]; if (first) first.focus(); });
        });
        backdrop.addEventListener('click', function () { close(true); });
        sidebar.addEventListener('click', function (event) { if (event.target.closest('[data-nav-close]')) close(true); });
        document.addEventListener('keydown', function (event) {
            if (!root.hasAttribute('data-nav-open')) return;
            if (event.key === 'Escape') { event.preventDefault(); close(true); }
            if (event.key === 'Tab') {
                var items = focusable(), first = items[0], last = items[items.length - 1];
                if (!items.length) return;
                if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
                else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
            }
        });
        var desktop = window.matchMedia('(min-width: 1024px)');
        desktop.addEventListener('change', function (event) { if (event.matches) close(false); });
        var path = location.pathname.replace(/\/$/, '');
        sidebar.querySelectorAll('a[href]').forEach(function (link) {
            var href = link.getAttribute('href');
            if (!href || href.charAt(0) === '#') return;
            var target = new URL(link.href, location.href);
            if (target.origin === location.origin && target.pathname.replace(/\/$/, '') === path && !target.hash) link.setAttribute('aria-current', 'page');
        });
    });
})();

/* Select2 replaces the native control; retain its existing form label. */
window.addEventListener('load', function () {
    document.querySelectorAll('.select2-selection[role="combobox"]').forEach(function (selection) {
        var container = selection.closest('.select2-container');
        var nativeControl = container && container.previousElementSibling;
        var label = nativeControl && nativeControl.labels && nativeControl.labels[0];
        if (label) {
            if (!label.id) label.id = nativeControl.id + '-aspm-label';
            selection.setAttribute('aria-labelledby', label.id);
        }
    });
});
