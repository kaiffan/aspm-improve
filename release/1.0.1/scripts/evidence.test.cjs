const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync('dojo/static/dojo/js/aspm-evidence.js', 'utf8');
function boot({saved = 0, hidden = false, status = 200, revision = 'same'} = {}) {
    let now = 1000000, requests = 0, reloads = 0;
    const timers = new Map(); let next = 0;
    const storage = new Map(saved ? [['aspm-evidence-poll:/state', String(saved)]] : []);
    const context = {
        document: {hidden, querySelector: () => ({dataset: {aspmStateUrl: '/state', aspmRevision: 'same'}})},
        Date: {now: () => now}, Number, String, AbortController,
        sessionStorage: {getItem: k => storage.get(k), setItem: (k, v) => storage.set(k, v)},
        setTimeout: (fn, ms) => {timers.set(++next, {fn, at: now + ms}); return next;},
        clearTimeout: id => timers.delete(id),
        fetch: async () => {requests++; return {ok: status === 200, redirected: false, json: async () => ({revision})};},
        window: {location: {reload: () => reloads++}}
    };
    vm.runInNewContext(source, context);
    return {
        async tick() {
            if (!timers.size) return false;
            const [id, timer] = [...timers].sort((a, b) => a[1].at - b[1].at)[0];
            timers.delete(id); now = timer.at; await timer.fn(); return true;
        },
        get requests() {return requests;}, get reloads() {return reloads;}, get timers() {return timers.size;}
    };
}
test('Evidence polling is bounded to five minutes', async () => {
    const browser = boot();
    for (let i = 0; i < 100; i++) if (!await browser.tick()) break;
    assert.ok(browser.requests <= 30 && browser.requests > 0);
    assert.equal(browser.timers, 0);
});
test('Evidence revision change reloads the page once', async () => {
    const browser = boot({revision: 'new'}); await browser.tick();
    assert.equal(browser.reloads, 1); assert.equal(browser.timers, 0);
});
test('Authorization failures stop evidence polling', async () => {
    const browser = boot({status: 403}); await browser.tick();
    assert.equal(browser.requests, 1); assert.equal(browser.timers, 0);
});
test('Expired polling budget survives page reload', async () => {
    const browser = boot({saved: 999999}); await browser.tick();
    assert.equal(browser.requests, 0); assert.equal(browser.timers, 0);
});
test('Hidden pages do not send evidence polling requests', async () => {
    const browser = boot({hidden: true});
    for (let i = 0; i < 50; i++) if (!await browser.tick()) break;
    assert.equal(browser.requests, 0); assert.equal(browser.timers, 0);
});
