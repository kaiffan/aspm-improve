/* Poll ScanRun/report metadata for at most five minutes, including across reloads. */
(function () {
    'use strict';
    const panel = document.querySelector('[data-aspm-state-url]');
    if (!panel) return;
    const key = 'aspm-evidence-poll:' + panel.dataset.aspmStateUrl;
    let deadline;
    try {
        deadline = Number(sessionStorage.getItem(key)) || Date.now() + 300000;
        sessionStorage.setItem(key, String(deadline));
    } catch (_) { deadline = Date.now() + 300000; }
    let requests = 0;
    async function poll() {
        if (Date.now() >= deadline || requests >= 30) return;
        if (!document.hidden) {
            requests += 1;
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 5000);
            try {
                const response = await fetch(panel.dataset.aspmStateUrl, {
                    credentials: 'same-origin', cache: 'no-store', signal: controller.signal
                });
                if (!response.ok || response.redirected) return;
                const state = await response.json();
                if (state.revision !== panel.dataset.aspmRevision) {
                    window.location.reload();
                    return;
                }
            } catch (_) { /* A later bounded poll can recover a transient failure. */ }
            finally { clearTimeout(timeout); }
        }
        setTimeout(poll, 10000);
    }
    setTimeout(poll, 10000);
}());
