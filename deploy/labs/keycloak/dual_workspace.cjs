const assert = require('node:assert/strict');
const { mkdirSync, readFileSync, writeFileSync } = require('node:fs');
const { join } = require('node:path');
const { chromium } = require('playwright');

const [state, output] = process.argv.slice(2);
const origin = 'https://localhost:48141';
const accounts = JSON.parse(readFileSync(join(state, 'accounts.json'))).accounts;
const projects = JSON.parse(readFileSync(join(state, 'projects.json')));
const checks = [];
const date = new Date().toISOString().slice(0, 10);
const stamp = Date.now();
const name = `Classic assessment ${stamp}`;
const fixture = Buffer.from(JSON.stringify({ findings: [{
  title: 'Synthetic Classic finding', description: 'Local assessment evidence', severity: 'Medium',
}] }));

async function login(browser, user, colorScheme = 'light') {
  const context = await browser.newContext({ ignoreHTTPSErrors: true, colorScheme, reducedMotion: 'reduce', viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  await page.goto(origin + '/sso/login');
  await page.locator('#username').fill(user);
  await page.locator('#password').fill(accounts[user].password);
  await page.locator('#kc-login').click();
  await page.waitForURL(origin + '/workspace/projects');
  const csrf = (await context.cookies(origin)).find(cookie => cookie.name === 'csrftoken');
  return { context, page, headers: { Origin: origin, 'X-CSRFToken': csrf.value } };
}

async function post(session, path, options, status, label) {
  const response = await session.context.request.post(origin + path, { ...options, headers: session.headers });
  assert.equal(response.status(), status, label);
  checks.push({ label, status });
  return response.json();
}

async function capture(page, label) {
  assert.ok(await page.locator('h1,h2,h3').count(), label);
  await page.waitForFunction(() => document.querySelector('.aspm-brand img')?.naturalWidth > 0);
  const layout = await page.evaluate(() => ({ width: innerWidth, scroll: document.documentElement.scrollWidth }));
  assert.ok(layout.scroll <= layout.width + 2, `Horizontal overflow on ${label}`);
  await page.screenshot({ path: join(output, label + '.png'), animations: 'disabled', fullPage: true });
  checks.push({ label, ...layout });
}

async function main() {
  mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ args: ['--host-resolver-rules=MAP aspm-keycloak.test 127.0.0.1', '--no-proxy-server'] });
  try {
    const secops = await login(browser, 'secops');
    const type = await post(secops, '/api/v2/product_types/', { data: { name: `Dual qualification ${stamp}` } }, 201, 'Product Type create');
    await post(secops, '/api/v2/products/', { data: { name: `Infrastructure ${stamp}`, description: 'Synthetic standalone assessment', prod_type: type.id } }, 201, 'Product create');
    const expert = await login(browser, 'expert');
    const engagement = await post(expert, '/api/v2/engagements/', { data: { name, product: projects.TEST.id, target_start: date, target_end: date } }, 201, 'Classic Engagement create');
    const scanType = 'Generic Findings Import';
    const file = { name: 'assessment.json', mimeType: 'application/json', buffer: fixture };
    const imported = await post(expert, '/api/v3/import', {
      multipart: { mode: 'import', engagement: String(engagement.id), scan_type: scanType, file },
    }, 200, 'Classic v3 import without Git');
    const classicTest = imported.test.id;
    await post(expert, '/api/v2/reimport-scan/', {
      multipart: { test: String(classicTest), scan_type: scanType, deduplication_execution_mode: 'sync', file },
    }, 201, 'Classic v2 reimport without Git');
    const finding = await post(expert, '/api/v2/findings/', { data: {
      test: classicTest, title: 'Manual local evidence', description: 'Test-only fixture', severity: 'Low',
      numerical_severity: 'S3', found_by: [], active: true, verified: false,
    } }, 201, 'Manual Finding create');
    const patched = await expert.context.request.patch(origin + `/api/v2/findings/${finding.id}/`, {
      data: { false_p: true }, headers: expert.headers,
    });
    assert.equal(patched.status(), 200);
    assert.equal((await patched.json()).false_p, true);
    checks.push({ label: 'Finding PATCH and False Positive', status: 200 });

    await expert.page.getByRole('link', { name: 'Classic Workspace', exact: true }).click();
    await expert.page.getByRole('heading', { name: 'Classic Workspace' }).waitFor();
    await capture(expert.page, 'classic-expert-desktop');
    assert.equal((await expert.page.goto(origin + `/test/${classicTest}`)).status(), 200);
    assert.equal(await expert.page.getByRole('link', { name: 'View originating ScanRun and commit' }).count(), 0);
    await capture(expert.page, 'classic-test-desktop');
    assert.equal((await expert.page.goto(origin + `/engagement/${engagement.id}`)).status(), 200);
    await capture(expert.page, 'classic-engagement-desktop');

    const reader = await login(browser, 'reader-test', 'dark');
    await reader.page.getByRole('link', { name: 'Classic Workspace', exact: true }).click();
    const classicProjects = await reader.page.locator('table tbody th a').allTextContents();
    assert.deepEqual(classicProjects, ['TEST']);
    assert.equal((await reader.page.goto(origin + '/product')).status(), 200);
    assert.deepEqual(await reader.page.locator('table tbody th a').allTextContents(), ['TEST']);
    checks.push({ label: 'Classic Product bookmark remains scoped after login', status: 200 });
    await reader.page.setViewportSize({ width: 390, height: 844 });
    await reader.page.waitForFunction(() => document.documentElement.dataset.theme === 'dark');
    await capture(reader.page, 'classic-reader-mobile-dark');
    const report = await reader.context.request.get(origin + `/test/${classicTest}/report?_generate=1&report_type=HTML`);
    assert.equal(report.status(), 200);
    assert.ok(/Synthetic Classic finding/i.test(await report.text()), 'Test report includes the imported Finding');
    const engagementReport = await reader.context.request.get(origin + `/engagement/${engagement.id}/report?_generate=1&report_type=HTML`);
    assert.equal(engagementReport.status(), 200);
    assert.ok(/Synthetic Classic finding/i.test(await engagementReport.text()), 'Engagement report includes the imported Finding');
    const payroll = await login(browser, 'reader-payments');
    const forbidden = await payroll.context.request.get(origin + `/api/v2/tests/${classicTest}/`);
    assert.equal(forbidden.status(), 404);
    checks.push({ label: 'Classic reports and cross-Product isolation', html: 200, cross_product: 404 });

    const commit = projects.TEST.repositories.backend.commits.a;
    const runs = await reader.context.request.get(origin + `/api/aspm/v1/commits/${commit}/scans/`);
    assert.equal(runs.status(), 200);
    const scan = (await runs.json()).find(row => row.test && row.status === 'COMPLETED');
    assert.ok(scan);
    assert.equal((await reader.page.goto(origin + `/commits/${commit}/evidence?tab=originals&run=${scan.id}`)).status(), 200);
    await capture(reader.page, 'devsecops-reader-mobile-dark');
    await reader.page.getByRole('link', { name: 'Linked Test', exact: true }).click();
    await reader.page.getByRole('link', { name: 'View originating ScanRun and commit' }).click();
    await reader.page.waitForURL(url => url.pathname.endsWith('/evidence') && url.searchParams.get('run') === scan.id);
    checks.push({ label: 'Bidirectional Test and ScanRun navigation', status: 200 });

    await expert.page.getByRole('link', { name: 'DevSecOps Workspace', exact: true }).click();
    await expert.page.waitForURL(origin + '/workspace/projects');
    await capture(expert.page, 'devsecops-expert-desktop');
  } finally {
    writeFileSync(join(output, 'browser.json'), JSON.stringify(checks, null, 2) + '\n');
    await browser.close();
  }
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
