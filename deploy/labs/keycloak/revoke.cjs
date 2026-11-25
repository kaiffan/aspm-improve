const assert = require('node:assert/strict');
const { readFileSync, writeFileSync } = require('node:fs');
const { join } = require('node:path');
const { chromium, request } = require('playwright');

const origin = 'https://localhost:48141';
const idp = 'https://localhost:48140';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function main() {
  const state = JSON.parse(readFileSync(join(process.argv[2], 'accounts.json')));
  const client = await request.newContext({ baseURL: idp, ignoreHTTPSErrors: true });
  const browser = await chromium.launch({ args: ['--host-resolver-rules=MAP aspm-keycloak.test 127.0.0.1', '--no-proxy-server'] });
  const results = [];
  const login = async () => {
    const context = await browser.newContext({ ignoreHTTPSErrors: true });
    const page = await context.newPage();
    await page.goto(origin + '/sso/login');
    await page.locator('#username').fill('reader-test');
    await page.locator('#password').fill(state.accounts['reader-test'].password);
    await page.locator('#kc-login').click();
    await page.waitForURL(origin + '/workspace/projects');
    return { context, page };
  };
  let groupPath;
  let removed = false;
  const adminHeaders = async () => {
    const issued = await client.post('/realms/master/protocol/openid-connect/token', { form: {
      grant_type: 'password', client_id: 'admin-cli', username: 'lab-admin', password: state.admin,
    } });
    assert.equal(issued.status(), 200);
    return { Authorization: 'Bearer ' + (await issued.json()).access_token };
  };
  try {
    const headers = await adminHeaders();
    const users = await client.get('/admin/realms/aspm-qualification/users?username=reader-test&exact=true', { headers });
    const groups = await client.get('/admin/realms/aspm-qualification/groups?search=devsecops-TEST-user&exact=true', { headers });
    const [user] = await users.json();
    const [group] = await groups.json();
    groupPath = `/admin/realms/aspm-qualification/users/${user.id}/groups/${group.id}`;
    const initial = await client.put(groupPath, { headers });
    assert.equal(initial.status(), 204);
    const active = await login();
    assert.equal(await active.page.getByRole('link', { name: 'TEST', exact: true }).count(), 1);
    const removal = await client.delete(groupPath, { headers: await adminHeaders() });
    assert.equal(removal.status(), 204);
    removed = true;
    const after = await login();
    assert.equal(await after.page.getByRole('link', { name: 'TEST', exact: true }).count(), 0);
    results.push({ stage: 'group-revoked-on-next-login', status: 'PASS' });
    const project = JSON.parse(readFileSync(join(process.argv[2], 'projects.json'))).TEST;
    const path = origin + `/api/aspm/v1/projects/${project.id}/repositories/`;
    const start = Date.now();
    const limit = Number(process.env.ASPM_LAB_GROUP_TTL || '120');
    let refusal;
    while (Date.now() - start <= (limit + 10) * 1000) {
      refusal = await active.context.request.get(path);
      if (refusal.status() !== 200) break;
      await sleep(1000);
    }
    assert.equal(refusal.status(), 403);
    results.push({ stage: 'active-session-revoked', status: 403, elapsed_seconds: (Date.now() - start) / 1000, ttl_seconds: limit });
  } finally {
    try {
      if (removed) {
        const restore = await client.put(groupPath, { headers: await adminHeaders() });
        assert.equal(restore.status(), 204);
      }
    } finally {
      writeFileSync(process.argv[3], JSON.stringify(results, null, 2) + '\n');
    }
    await client.dispose();
    await browser.close();
  }
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
