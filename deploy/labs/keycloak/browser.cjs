const assert = require('node:assert/strict');
const { readFileSync, mkdirSync, writeFileSync } = require('node:fs');
const { join, resolve } = require('node:path');
const { chromium, request } = require('playwright');

const state = resolve(process.argv[2]);
const output = resolve(process.argv[3]);
const root = resolve(__dirname, '../../..');
const accounts = JSON.parse(readFileSync(join(state, 'accounts.json'))).accounts;
const projects = JSON.parse(readFileSync(join(state, 'projects.json')));
const origin = 'https://localhost:48141';
const checks = [];
const stamp = Date.now();
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function authenticated(browser, name) {
  const context = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  await page.goto(origin + '/sso/login');
  await page.locator('#username').fill(name);
  await page.locator('#password').fill(accounts[name].password);
  await page.locator('#kc-login').click();
  await page.waitForURL(origin + '/workspace/projects');
  checks.push({ stage: 'authorization-code-pkce', principal: name, status: 200 });
  return { context, page };
}

async function settled(api, path, acceptable) {
  const deadline = Date.now() + 45000;
  while (Date.now() < deadline) {
    const response = await api.get(path);
    assert.equal(response.status(), 200);
    const payload = await response.json();
    if (acceptable(payload)) return payload;
    await sleep(300);
  }
  throw new Error('Worker result timed out');
}

async function postScan(api, project, repository, char, label, file, key) {
  const response = await api.post('/api/aspm/v1/scans/', {
    headers: { 'Idempotency-Key': key },
    multipart: {
      project_id: String(project.id), repository_url: repository.url, commit_sha: char.repeat(40),
      scanner_type: label, scanner_version: 'fixture', branch: 'main', pipeline_id: `qualification-${stamp}`,
      file: { name: file.split('/').at(-1), mimeType: 'application/octet-stream', buffer: readFileSync(join(root, 'unittests/scans', file)) },
    },
  });
  assert.equal(response.status(), 202);
  const accepted = await response.json();
  const scan = await settled(api, `/api/aspm/v1/scans/${accepted.id}/`, item => ['COMPLETED', 'FAILED'].includes(item.status));
  assert.equal(scan.status, 'COMPLETED', scan.error_code);
  assert.ok(scan.finding_count > 0);
  checks.push({ stage: 'ci-worker', scanner: label, status: scan.status, findings: scan.finding_count });
  return scan;
}

async function capture(session, name) {
  for (const [width, height, theme] of [[1440, 1000, 'light'], [820, 1060, 'light'], [390, 844, 'dark']]) {
    await session.page.setViewportSize({ width, height });
    await session.page.emulateMedia({ colorScheme: theme });
    await session.page.waitForFunction(() => document.querySelector('.aspm-brand img')?.naturalWidth > 0);
    const check = await session.page.evaluate(() => ({
      width: innerWidth, scroll: document.documentElement.scrollWidth, heading: Boolean(document.querySelector('h1,h2,h3,h4,[role=heading]')),
      stylesheet: Array.from(document.styleSheets).some(sheet => sheet.href?.includes('tailwind-out.css') && sheet.cssRules.length > 0),
    }));
    assert.ok(check.stylesheet, 'Compiled application stylesheet is missing');
    const contrast = await session.page.waitForFunction(() => {
      const luminance = rgb => rgb.match(/[0-9.]+/g).slice(0, 3).map(value => {
        const channel = Number(value) / 255;
        return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
      }).reduce((sum, value, index) => sum + value * [0.2126, 0.7152, 0.0722][index], 0);
      const controls = document.querySelectorAll('.aspm-workspace-form input, .aspm-workspace-form .btn-secondary, #simple_search_submit');
      const minimum = Math.min(...Array.from(controls, element => {
        const style = getComputedStyle(element);
        const [lower, higher] = [luminance(style.color), luminance(style.backgroundColor)].sort((a, b) => a - b);
        return (higher + 0.05) / (lower + 0.05);
      }));
      return minimum >= 4.5 ? minimum : false;
    }, undefined, { timeout: 4000 });
    const minimumContrast = await contrast.jsonValue();
    assert.ok(check.heading, `No heading on ${name}`);
    assert.ok(check.scroll <= check.width + 2, `Horizontal overflow on ${name} at ${width}`);
    await session.page.screenshot({ path: join(output, `${name}-${width}-${theme}.png`), fullPage: true });
    checks.push({ stage: 'browser-layout', page: name, width, theme, form_contrast_minimum: Number(minimumContrast.toFixed(2)) });
  }
}

async function main() {
  mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ args: ['--host-resolver-rules=MAP aspm-keycloak.test 127.0.0.1', '--no-proxy-server'] });
  const api = await request.newContext({ baseURL: origin, ignoreHTTPSErrors: true, extraHTTPHeaders: { Authorization: `ASPM ${projects.TEST.token}` } });
  try {
    const secops = await authenticated(browser, 'secops');
    const backend = projects.TEST.repositories.backend;
    await secops.page.getByRole('row').filter({ hasText: 'TEST' }).getByRole('link', { name: 'Engagement policy' }).click();
    await secops.page.locator('#id_strategy').selectOption('repository');
    await secops.page.getByRole('button', { name: 'Save policy' }).click();
    await secops.page.getByText('An override is configured for this scope.').waitFor();
    checks.push({ stage: 'secops-engagement-policy', status: 200 });
    const formats = [
      ['Semgrep JSON Report', 'semgrep/one_finding.json'],
      ['Trivy Scan', 'trivy/scheme_2_many_vulns.json'],
      ['Dependency Track Finding Packaging Format (FPF) Export', 'dependency_track/one_finding.json'],
      ['KICS Scan', 'kics/many_findings.json'],
      ['Fortify Scan', 'fortify/fortify_few_findings.xml'],
      ['ffuf Scan', 'ffuf/ffuf_one_vuln.json'],
    ];
    const scans = [];
    for (const [label, file] of formats) {
      scans.push(await postScan(api, projects.TEST, backend, 'a', label, file, `${stamp}-${scans.length}`));
    }
    await postScan(api, projects.TEST, backend, 'b', ...formats[0], `${stamp}-next-commit`);
    const commitPath = `/commits/${backend.commits.a}/evidence`;
    const exportResponse = await api.post(`/api/aspm/v1/commits/${backend.commits.a}/reports/`, { data: { scan_ids: scans.map(scan => scan.id) } });
    assert.equal(exportResponse.status(), 202);
    const reportId = (await exportResponse.json()).id;
    await settled(api, `/api/aspm/v1/commits/${backend.commits.a}/reports/`, reports => reports.some(report => report.id === reportId && report.status === 'COMPLETED'));
    const original = await api.get(`/api/aspm/v1/scans/${scans[0].id}/artifact/`);
    assert.equal(original.status(), 200);
    assert.deepEqual(await original.body(), readFileSync(join(root, 'unittests/scans', formats[0][1])));

    await secops.page.reload();
    await secops.page.getByRole('heading', { name: 'Managed Engagements' }).waitFor();
    await capture(secops, 'secops-engagement');
    const expert = await authenticated(browser, 'expert');
    let response = await expert.context.request.get(origin + '/system_settings');
    assert.equal(response.status(), 403);
    assert.equal((await expert.page.goto(origin + '/finding')).status(), 200);
    assert.ok((await expert.page.getByRole('link', { name: 'Findings', exact: true }).count()) > 0);
    const originalReport = await api.get(`/api/aspm/v1/reports/${reportId}/download/?format=json`);
    const originalEvidence = await originalReport.json();
    const target = originalEvidence.observations.find(item => item.scanner === 'Semgrep JSON Report');
    const csrf = (await expert.context.cookies(origin)).find(cookie => cookie.name === 'csrftoken').value;
    response = await expert.context.request.patch(origin + `/api/v2/findings/${target.id}/`, {
      headers: { Origin: origin, 'X-CSRFToken': csrf }, data: { false_p: true },
    });
    assert.equal(response.status(), 200);
    assert.equal((await response.json()).false_p, true);
    const fixedEvidence = await api.get(`/api/aspm/v1/reports/${reportId}/download/?format=json`);
    assert.deepEqual(await fixedEvidence.json(), originalEvidence);
    checks.push({ stage: 'expert-triage-immutable-observation', status: 200 });
    await capture(expert, 'expert-findings');

    for (const [reader, expected] of [
      ['reader-test', ['TEST']], ['reader-payments', ['PAYMENTS']],
      ['reader-both', ['PAYMENTS', 'TEST']], ['reader-none', []],
    ]) {
      const session = await authenticated(browser, reader);
      const names = await session.page.locator('table tbody th a').allTextContents();
      assert.deepEqual(names.sort(), expected);
      const visible = expected.includes('TEST');
      response = await session.context.request.get(origin + `/api/aspm/v1/reports/${reportId}/download/?format=json`);
      assert.equal(response.status(), visible ? 200 : 404);
      if (visible) {
        const evidence = await response.json();
        assert.equal(new Set(evidence.observations.map(item => item.scanner)).size, 6);
      }
      response = await session.context.request.get(origin + `/api/aspm/v1/scans/${scans[0].id}/artifact/`);
      assert.equal(response.status(), visible ? 200 : 404);
      checks.push({ stage: 'role-project-report-artifact', reader, projects: names, reportStatus: visible ? 200 : 404 });
      if (reader === 'reader-test') {
        await capture(session, 'user-projects');
        await session.page.goto(origin + commitPath + '?tab=reports');
        await session.page.getByRole('heading', { name: 'Commit evidence' }).waitFor();
        assert.equal(await session.page.getByRole('button', { name: /Generate fixed/ }).count(), 0);
        await capture(session, 'user-report');
      }
      await session.context.close();
    }
    checks.push({ stage: 'zero-finalize-generated-report', status: 'COMPLETED', scannerCount: scans.length });
  } finally {
    writeFileSync(join(output, 'browser.json'), JSON.stringify(checks, null, 2) + '\n');
    await api.dispose();
    await browser.close();
  }
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
