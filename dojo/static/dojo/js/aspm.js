/* ASPM shell: accessible mobile navigation; no network requests or dependencies. */
(function () {
    'use strict';
    document.addEventListener('DOMContentLoaded', function () {
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
            var target = new URL(link.href, location.href);
            if (target.origin === location.origin && target.pathname.replace(/\/$/, '') === path && !target.hash) link.setAttribute('aria-current', 'page');
        });
    });
})();
