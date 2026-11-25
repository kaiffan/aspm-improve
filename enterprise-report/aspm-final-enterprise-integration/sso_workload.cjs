const assert = require('node:assert/strict');
const { readFileSync, writeFileSync } = require('node:fs');
const { join } = require('node:path');
const { chromium, request } = require('playwright');

const [mode, state, output] = process.argv.slice(2);
const origin = 'https://localhost:48141';
const accounts = JSON.parse(readFileSync(join(state, 'accounts.json'))).accounts;
const projects = JSON.parse(readFileSync(join(state, 'projects.json')));
const browserOptions = { args: ['--host-resolver-rules=MAP aspm-keycloak.test 127.0.0.1', '--no-proxy-server'] };

async function signIn(browser, user) {
  const start = Date.now();
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await context.newPage();
  await page.goto(origin + '/sso/login');
  await page.locator('#username').fill(user);
  await page.locator('#password').fill(accounts[user].password);
  await page.locator('#kc-login').click();
  await page.waitForURL(origin + '/workspace/projects');
  const visible = await page.locator('table tbody th a').allTextContents();
  return { context, visible: visible.sort(), elapsed_ms: Date.now() - start };
}

async function concurrent() {
  const browser = await chromium.launch(browserOptions);
  try {
    return await Promise.all([
      ['secops', ['PAYMENTS', 'TEST']],
      ['expert', ['PAYMENTS', 'TEST']],
      ['reader-test', ['TEST']],
      ['reader-payments', ['PAYMENTS']],
      ['reader-both', ['PAYMENTS', 'TEST']],
      ['reader-none', []],
    ].map(async ([user, expected]) => {
      const { context, visible, elapsed_ms } = await signIn(browser, user);
      assert.deepEqual(visible, expected);
      await context.close();
      return { user, visible, elapsed_ms };
    }));
  } finally {
    await browser.close();
  }
}

async function establish() {
  const browser = await chromium.launch(browserOptions);
  try {
    const { context, visible } = await signIn(browser, 'reader-test');
    assert.deepEqual(visible, ['TEST']);
    await context.storageState({ path: join(state, 'outage-private-session.json') });
  } finally {
    await browser.close();
  }
}

async function outage() {
  const client = await request.newContext({
    baseURL: origin, ignoreHTTPSErrors: true, storageState: join(state, 'outage-private-session.json'),
  });
  const start = Date.now();
  const path = `/api/aspm/v1/projects/${projects.TEST.id}/repositories/`;
  try {
    assert.equal((await client.get(path)).status(), 200);
    const deadline = start + 130000;
    let status = 200;
    while (status === 200 && Date.now() < deadline) {
      await new Promise(resolve => setTimeout(resolve, 1500));
      status = (await client.get(path)).status();
    }
    assert.equal(status, 403);
    return { previously_valid_session_status: 200, status_after_claim_expiry: status, elapsed_seconds: (Date.now() - start) / 1000 };
  } finally {
    await client.dispose();
  }
}

async function main() {
  if (mode === 'establish') {
    await establish();
    return;
  }
  const result = mode === 'concurrent' ? await concurrent() : await outage();
  writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
