/* Ten closed-loop VUs; real browser reads + three native API operations per block. */
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const zlib = require('node:zlib');
const assert = require('node:assert/strict');
const { performance } = require('node:perf_hooks');
const { chromium } = require('playwright');

const config = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const accounts = JSON.parse(fs.readFileSync(config.accounts, 'utf8'));
const base = new URL(config.url);
assert.equal(base.hostname, '127.0.0.1');
assert.equal(accounts.length, 10);
assert.equal(new Set(accounts.map(a => a.token)).size, 10);
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const tasks = new Map(), offsets = new Map(), lastPublish = new Map();
const ledger = new Map();
const samples = [], httpSamples = [], concurrency = [];
let apiFlight = 0, browserFlight = 0, businessFlight = 0, stop = false;
let browser, server;
let warmReady = 0, measuredStart = null;
fs.mkdirSync(config.artifacts, { recursive: true });
const sampleFile = fs.openSync(config.output + '.samples.jsonl', 'a');
const httpFile = fs.openSync(config.output + '.http.jsonl', 'a');
const concurrencyFile = fs.openSync(config.output + '.concurrency.jsonl', 'a');

function concurrencyEvent() {
  const row = { at: Date.now() / 1000, api_requests: apiFlight, browser_requests: browserFlight,
    total_http_requests: apiFlight + browserFlight, active_business_operations: businessFlight };
  concurrency.push(row);
  fs.appendFileSync(concurrencyFile, JSON.stringify(row) + '\n');
}
function readTelemetry() {
  for (const name of fs.readdirSync(config.telemetry).filter(n => /^(app|worker)-\d+\.jsonl$/.test(n))) {
    const file = path.join(config.telemetry, name);
    const state = offsets.get(file) || { offset: 0, pending: '' };
    const size = fs.statSync(file).size;
    if (size === state.offset) continue;
    const fd = fs.openSync(file, 'r');
    const bytes = Buffer.alloc(size - state.offset);
    fs.readSync(fd, bytes, 0, bytes.length, state.offset); fs.closeSync(fd);
    state.offset = size;
    const lines = (state.pending + bytes.toString('utf8')).split('\n');
    state.pending = lines.pop(); offsets.set(file, state);
    for (const line of lines) {
      if (!line) continue;
      const row = JSON.parse(line);
      if (row.database !== config.database || !row.task_id) continue;
      const task = tasks.get(row.task_id) || { id: row.task_id };
      if (row.opid) task.opid = row.opid;
      task.name = row.task || task.name;
      if (row.event === 'task_publish') { task.published = row.at; lastPublish.set(task.opid, row.at); }
      if (row.event === 'task_end') { task.state = row.state; task.ended = row.at; }
      tasks.set(row.task_id, task);
    }
  }
}
async function background(opid, requireTasks = false) {
  const start = Date.now();
  while (!stop && Date.now() - start < 240000) {
    readTelemetry();
    const owned = [...tasks.values()].filter(t => t.opid === opid);
    assert.ok(!owned.some(t => t.state === 'FAILURE'), 'Real Celery task failed');
    if ((!requireTasks || owned.length) && owned.every(t => t.state === 'SUCCESS') &&
        Date.now() / 1000 - (lastPublish.get(opid) || start / 1000) >= 0.25) return owned;
    await sleep(100);
  }
  throw new Error('Background completion not confirmed within 240 seconds');
}
async function request(account, method, endpoint, body, opid, contentType = 'application/json') {
  const payload = body == null ? undefined : Buffer.isBuffer(body) ? body : Buffer.from(JSON.stringify(body));
  const start = performance.now(), at = Date.now() / 1000;
  apiFlight++; concurrencyEvent();
  let sendMs = null;
  try {
    return await new Promise((resolve, reject) => {
      const req = http.request({ hostname: base.hostname, port: base.port, path: endpoint, method,
        timeout: 240000, agent: account.agent,
        headers: { Authorization: 'Token ' + account.token, 'X-Acceptance-Operation': opid,
          Accept: '*/*', ...(payload ? { 'Content-Type': contentType, 'Content-Length': payload.length } : {}) } }, response => {
        const chunks = [];
        response.on('data', chunk => chunks.push(chunk));
        response.on('end', () => {
          const data = Buffer.concat(chunks), duration = performance.now() - start;
          const observation = { at, ended_at: Date.now() / 1000, opid, method, path: endpoint,
            status: response.statusCode, bytes: data.length, ms: duration, client_socket_send_ms: sendMs,
            view_ms: Number(response.headers['x-acceptance-view-ms']) || null,
            sql_ms: Number(response.headers['x-acceptance-sql-ms']) || null,
            sql_count: Number(response.headers['x-acceptance-sql-count']) || null };
          httpSamples.push(observation); fs.appendFileSync(httpFile, JSON.stringify(observation) + '\n');
          resolve({ status: response.statusCode, body: data, headers: response.headers, observation });
        });
        response.on('error', reject);
      });
      req.on('error', reject); req.on('timeout', () => req.destroy(new Error('HTTP timeout')));
      const send = performance.now();
      req.end(payload, () => { sendMs = performance.now() - send; });
    });
  } finally { apiFlight--; concurrencyEvent(); }
}
function jsonResponse(response, status) {
  const data = JSON.parse(response.body);
  assert.equal(response.status, status, 'Unexpected real HTTP status: ' + JSON.stringify(Object.fromEntries(Object.entries(data).filter(([key]) => key !== 'pro'))).slice(0, 1000));
  return data;
}
function multipart(fields, payload, namespace) {
  const boundary = 'acceptance-' + namespace;
  const parts = [];
  for (const [key, value] of Object.entries(fields)) parts.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="${key}"\r\n\r\n${value}\r\n`));
  parts.push(Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="${namespace}.xml"\r\nContent-Type: application/xml\r\n\r\n`));
  parts.push(payload, Buffer.from(`\r\n--${boundary}--\r\n`));
  return { body: Buffer.concat(parts), contentType: 'multipart/form-data; boundary=' + boundary };
}
function reportIds(html) {
  assert.ok(/<!doctype html/i.test(html) && /<\/html>/i.test(html), 'Incomplete HTML report document');
  const ids = [];
  for (const block of html.split('<div class="panel-heading finding-title">')) {
    if (!/<h5>\s*Finding \d+:/i.test(block)) continue;
    const table = block.match(/<table id="notes"[^>]*>([\s\S]*?)<\/table>/);
    assert.ok(table, 'Finding report table absent');
    const rows = [...table[1].matchAll(/<tr>([\s\S]*?)<\/tr>/g)].map(m => m[1]);
    const text = value => value.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
    const headers = [...rows[0].matchAll(/<th[^>]*>([\s\S]*?)<\/th>/g)].map(m => text(m[1]));
    const cells = [...rows[1].matchAll(/<td(?:\s[^>]*)?>([\s\S]*?)<\/td>/g)].map(m => text(m[1]));
    const id = Number(cells[headers.indexOf('Dojo ID')]);
    assert.ok(Number.isSafeInteger(id) && id > 0, 'Report Finding ID not found'); ids.push(id);
  }
  assert.equal(new Set(ids).size, ids.length, 'Duplicate report rows');
  return ids;
}
function order(vu, block) {
  let state = (config.seed + vu * 1009 + block * 7919) >>> 0;
  const random = () => { state = (Math.imul(state, 1664525) + 1013904223) >>> 0; return state / 4294967296; };
  const values = ['open', 'import', 'create', 'export'];
  for (let i = values.length - 1; i > 0; i--) { const j = Math.floor(random() * (i + 1)); [values[i], values[j]] = [values[j], values[i]]; }
  if (values.indexOf('create') > values.indexOf('export')) {
    const a = values.indexOf('create'), b = values.indexOf('export'); [values[a], values[b]] = [values[b], values[a]];
  }
  return values;
}

async function vuRun(account) {
  account.agent = new http.Agent({ keepAlive: true, maxSockets: 1 });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, colorScheme: 'light' });
  const mode = ['light', 'dark', 'system'][account.vu % 3];
  await context.addInitScript(value => localStorage.setItem('aspm.theme', value), mode);
  await context.addCookies([{ name: 'sessionid', value: account.session, domain: base.hostname, path: '/', httpOnly: true, sameSite: 'Lax' }]);
  const page = await context.newPage();
  const active = new Set();
  page.on('request', r => { active.add(r); browserFlight++; concurrencyEvent(); });
  function ended(r) { if (active.delete(r)) { browserFlight--; concurrencyEvent(); } }
  page.on('requestfinished', ended); page.on('requestfailed', ended);
  try {
    if (config.readonly_warmup) {
      const finding = (account.products[0] - 1) * 500000 + 1;
      await page.setExtraHTTPHeaders({ 'X-Acceptance-Operation': `${config.run}:warmup:v${account.vu}` });
      const response = await page.goto(config.url + `/finding/${finding}`, { waitUntil: 'domcontentloaded', timeout: 120000 });
      assert.equal(response.status(), 200);
      await page.locator('#vuln_desc').waitFor({ state: 'visible', timeout: 120000 });
    }
    if (config.start_file) {
      warmReady++;
      if (warmReady === (config.vus || 10)) fs.writeFileSync(config.output + '.ready.json', JSON.stringify({ at: Date.now() / 1000, vus_ready: warmReady }));
      while (!fs.existsSync(config.start_file)) {
        if (fs.existsSync(config.stop_file)) throw new Error('Guard stopped run before measurement');
        await sleep(20);
      }
    }
    if (measuredStart === null) measuredStart = Date.now() / 1000;
    for (let block = 0; block < config.blocks && !stop; block++) {
      const product = account.products[block % account.products.length];
      const engagement = (product - 1) * 5 + block % 5 + 1;
      const targetTest = (engagement - 1) * 250 + 1;
      let created = null;
      for (const operation of order(account.vu, block)) {
        if (stop || fs.existsSync(config.stop_file)) throw new Error('Run stopped; preserve partial observations');
        const opid = `${config.run}:v${account.vu}:b${block}:${operation}`;
        const row = { run: config.run, variant: config.variant, repeat: config.repeat, vu: account.vu,
          block, operation, opid, started_at: Date.now() / 1000, product, engagement, target_test: targetTest };
        const begin = performance.now(); businessFlight++; concurrencyEvent();
        try {
          if (operation === 'create') {
            const payload = { test: targetTest, title: `Acceptance Finding ${account.vu + 1} ${block + 1}`,
              severity: ['Critical', 'High', 'Medium', 'Low', 'Info'][block % 5], cwe: 79,
              numerical_severity: 'S' + (block % 5),
              description: 'Created through native REST API during mixed acceptance workload.',
              mitigation: 'Apply input validation and least privilege.', references: 'https://acceptance.invalid/reference',
              date: '2026-11-12', active: true, verified: true, dynamic_finding: true, static_finding: false,
              found_by: [config.scan_type_id], push_to_jira: false };
            const response = await request(account, 'POST', '/api/v2/findings/', payload, opid);
            const data = jsonResponse(response, 201);
            assert.ok(data.id > 1000000); assert.equal(data.test, targetTest); assert.equal(data.title, payload.title); assert.equal(data.severity, payload.severity);
            row.http_ms = response.observation.ms; row.finding_id = data.id;
            created = data.id;
            const existing = ledger.get(targetTest) || []; existing.push({ id: data.id, at: response.observation.ended_at }); ledger.set(targetTest, existing);
            const actual = jsonResponse(await request(account, 'GET', `/api/v2/findings/${data.id}/`, null, opid), 200);
            assert.equal(actual.id, data.id); assert.equal(actual.test, targetTest); assert.equal(actual.title, payload.title);
            const backgroundStart = performance.now(); row.tasks = (await background(opid)).length;
            row.background_observed_ms = performance.now() - backgroundStart;
            row.valid = true;
          } else if (operation === 'import') {
            const name = `vu${String(account.vu + 1).padStart(2, '0')}-b${String(block + 1).padStart(2, '0')}`;
            const payload = zlib.gunzipSync(fs.readFileSync(path.join(config.scans, name + '.xml.gz')));
            const upload = multipart({ engagement, scan_type: 'ZAP Scan', test_title: 'Import ' + name,
              active: 'true', verified: 'true', minimum_severity: 'Info', push_to_jira: 'false',
              environment: 'Acceptance isolated',
              deduplication_execution_mode: 'async', auto_create_context: 'false' }, payload, name);
            const response = await request(account, 'POST', '/api/v2/import-scan/', upload.body, opid, upload.contentType);
            const data = jsonResponse(response, 201); const test = data.test || data.test_id;
            assert.ok(test && test > 2500); row.test_id = test; row.http_ms = response.observation.ms;
            row.upload_client_socket_ms = response.observation.client_socket_send_ms;
            row.scan_bytes = payload.length; row.scan_sha256 = crypto.createHash('sha256').update(payload).digest('hex');
            row.deduplication_complete_at_http_response = data.deduplication_complete ?? null;
            const waiting = performance.now(); row.tasks = (await background(opid, true)).length;
            row.background_observed_ms = performance.now() - waiting;
            const findings = jsonResponse(await request(account, 'GET', `/api/v2/findings/?test=${test}&limit=1`, null, opid), 200);
            assert.equal(findings.count, 400); row.findings = findings.count;
            const duplicates = jsonResponse(await request(account, 'GET', `/api/v2/findings/?test=${test}&duplicate=true&limit=1`, null, opid), 200);
            assert.equal(duplicates.count, 0); row.duplicates = 0;
            const actualTest = jsonResponse(await request(account, 'GET', `/api/v2/tests/${test}/`, null, opid), 200);
            assert.equal(actualTest.engagement, engagement); assert.equal(actualTest.percent_complete, 100);
            row.valid = true;
          } else if (operation === 'export') {
            assert.ok(created, 'Export must include this VU/block committed creation');
            const required = (ledger.get(targetTest) || []).filter(item => item.at <= row.started_at).map(item => item.id);
            const response = await request(account, 'POST', `/api/v2/tests/${targetTest}/generate_report/`,
              { report_type: 'HTML', include_finding_notes: true, include_finding_images: true,
                include_executive_summary: true, include_table_of_contents: true }, opid);
            assert.equal(response.status, 200); assert.ok(response.headers['content-type'].includes('text/html'));
            const ids = reportIds(response.body.toString('utf8')), actual = new Set(ids);
            for (let offset = 1; offset <= 400; offset++) assert.ok(actual.has((targetTest - 1) * 400 + offset), 'Missing original Finding in report');
            for (const id of required) assert.ok(actual.has(id), 'Missing creation committed before report request');
            assert.ok(actual.has(created));
            const allowed = new Set((ledger.get(targetTest) || []).map(item => item.id));
            for (const id of ids) assert.ok(id <= 1000000 || allowed.has(id), 'Unexpected report Finding');
            assert.ok(response.body.includes(Buffer.from('Apply input validation and least privilege.')));
            const artifact = `${opid.replaceAll(':', '_')}.html.gz`;
            fs.writeFileSync(path.join(config.artifacts, artifact), zlib.gzipSync(response.body));
            row.report_ids = ids; row.required_created_ids = required; row.created_id = created;
            row.report_rows = ids.length; row.report_bytes = response.body.length; row.artifact = artifact;
            row.report_sha256 = crypto.createHash('sha256').update(response.body).digest('hex');
            row.http_ms = response.observation.ms; row.valid = true;
          } else {
            const test = (product - 1) * 1250 + (account.vu * 137 + block * 197) % 1250 + 1;
            const offset = block % 5 + Math.floor(block / 5) * 5;
            const finding = (test - 1) * 400 + offset + 1;
            const title = `Acceptance seed ${String(finding).padStart(7, '0')} ${['Critical', 'High', 'Medium', 'Low', 'Info'][offset % 5]}`;
            await page.setExtraHTTPHeaders({ 'X-Acceptance-Operation': opid });
            const navigationStart = performance.now(); row.navigation_started_at = Date.now() / 1000;
            const response = await page.goto(config.url + `/finding/${finding}`, { waitUntil: 'domcontentloaded', timeout: 120000 });
            assert.equal(response.status(), 200);
            await page.locator('h3.finding-title').filter({ hasText: title }).waitFor({ state: 'visible', timeout: 120000 });
            await page.locator('#vuln_desc').waitFor({ state: 'visible', timeout: 120000 });
            assert.ok((await page.locator('#vuln_desc').innerText()).includes('Deterministic finding'));
            const ready = performance.now();
            row.browser_ready_ms = ready - navigationStart; row.finding_id = finding; row.source_test = test;
            await response.finished();
            const headers = await response.allHeaders(); row.server_view_ms = Number(headers['x-acceptance-view-ms']) || null;
            const timing = response.request().timing(); row.navigation_document_timing = timing;
            row.server_document_ms = timing.responseEnd >= 0 ? timing.responseEnd - timing.requestStart : null;
            row.theme = await page.locator('html').getAttribute('data-theme');
            row.valid = true;
          }
          row.e2e_ms = performance.now() - begin; row.ended_at = Date.now() / 1000;
          row.acceptance_ms = operation === 'create' ? row.http_ms : operation === 'open' ? row.browser_ready_ms : row.e2e_ms;
          samples.push(row); fs.appendFileSync(sampleFile, JSON.stringify(row) + '\n');
          console.log(operation, account.vu, block, Math.round(row.acceptance_ms), 'ms', 'verified');
        } catch (error) {
          row.valid = false; row.error = error.message; row.e2e_ms = performance.now() - begin; row.ended_at = Date.now() / 1000;
          samples.push(row); fs.appendFileSync(sampleFile, JSON.stringify(row) + '\n'); stop = true;
          fs.writeFileSync(config.stop_file, 'Business operation/validation failed; inspect preserved evidence\n'); throw error;
        } finally { businessFlight--; concurrencyEvent(); }
        await sleep(config.think_ms);
      }
    }
  } finally { await context.close(); account.agent.destroy(); }
}

(async () => {
  const started = Date.now() / 1000;
  server = await chromium.launchServer({ headless: true, args: ['--disable-background-networking'] });
  fs.writeFileSync(config.output + '.chrome.json', JSON.stringify({ pid: server.process().pid, at: started }));
  browser = await chromium.connect(server.wsEndpoint());
  const timer = setInterval(readTelemetry, 100);
  const results = await Promise.allSettled(accounts.slice(0, config.vus || 10).map(vuRun));
  clearInterval(timer); readTelemetry();
  const browserVersion = browser.version();
  await browser.close(); await server.close();
  const failures = results.filter(r => r.status === 'rejected').map(r => r.reason.message);
  const result = { run: config.run, variant: config.variant, repeat: config.repeat, vus: config.vus || 10,
    blocks_per_vu: config.blocks, think_ms: config.think_ms, process_started_at: started, started_at: measuredStart || started, ended_at: Date.now() / 1000,
    samples, failures, stopped: stop || failures.length > 0,
    requests: httpSamples.length, max_http_inflight: Math.max(...concurrency.map(r => r.total_http_requests)),
    max_business_inflight: Math.max(...concurrency.map(r => r.active_business_operations)),
    browser: browserVersion, model: 'One browser context per VU; browser Finding open plus import/create/report HTTP APIs; create precedes export in each balanced block' };
  fs.writeFileSync(config.output, JSON.stringify(result, null, 2) + '\n');
  for (const fd of [sampleFile, httpFile, concurrencyFile]) fs.closeSync(fd);
  if (failures.length) throw new Error(failures.join('; '));
  console.log('COMPLETE', config.run, samples.length, 'validated business operations');
})().catch(async error => {
  console.error(error.message);
  if (browser) await browser.close().catch(() => {});
  if (server) await server.close().catch(() => {});
  process.exitCode = 1;
});
