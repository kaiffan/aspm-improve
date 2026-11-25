/* Real HTTP browser regression. Credentials are read only from a private local fixture file. */
const fs = require('fs');
const path = require('path');
const {chromium} = require(path.resolve(__dirname, '../../release/1.0.1/browser/node_modules/playwright'));
const axePath = path.resolve(__dirname, '../../release/1.0.1/browser/node_modules/axe-core/axe.min.js');
const base = process.env.ASPM_TEST_URL || 'http://127.0.0.1:48135';
(async () => {
  const account = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch({headless: true});
  const context = await browser.newContext();
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const results = [];
  try {
    await page.goto(base + '/login');
    await page.locator('[name=username]').fill(account.username);
    await page.locator('[name=password]').fill(account.password);
    await Promise.all([page.waitForURL(url => !url.pathname.includes('/login')), page.locator('button[type=submit], input[type=submit]').first().click()]);
    for (const [width, height] of [[1440, 1000], [390, 844]]) {
      await page.setViewportSize({width, height});
      for (const theme of ['light', 'dark', 'system']) {
        for (const [name, route] of [
          ['webhooks', '/settings/integrations/webhooks/'],
          ['webhook-form', '/settings/integrations/webhooks/new/'],
          ['webhook-history', `/settings/integrations/webhooks/${account.subscription_id}/`],
          ['commit', `/commits/${account.commit_id}/evidence`],
          ['scanner-reports', `/commits/${account.commit_id}/evidence?tab=originals`],
          ['generated-reports', `/commits/${account.commit_id}/evidence?tab=reports`],
          ['historical-findings', `/commits/${account.commit_id}/evidence?tab=findings`],
          ['commit-changes', `/commits/${account.commit_id}/evidence?tab=changes`],
          ['dashboard', '/dashboard'],
          ['projects', '/product'],
          ['profile', '/profile'],
        ]) {
          const response = await page.goto(base + route);
          if (response.status() !== 200) throw new Error(`${route}: HTTP ${response.status()}`);
          await page.evaluate(async theme => { window.ASPMTheme.set(theme); await new Promise(requestAnimationFrame); await Promise.all(document.getAnimations().filter(a => a.effect.getTiming().iterations !== Infinity).map(a => a.finished.catch(() => {}))); }, theme);
          const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 2);
          if (overflow) throw new Error(`${name} ${width} ${theme}: horizontal overflow`);
          await page.addScriptTag({path: axePath});
          const violations = await page.evaluate(async () => (await axe.run(document.querySelector('#base-content') || document.body, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa']}})).violations.map(v => ({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary,html:n.html}))})));
          results.push({name,width,height,theme,http:response.status(),overflow,violations});
          if (['webhooks','commit'].includes(name) && theme !== 'system') await page.screenshot({path:path.join(__dirname, 'raw', `${name}-${width}-${theme}.png`),fullPage:true});
        }
      }
    }
    await page.goto(base + `/commits/${account.commit_id}/evidence`);
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    await page.getByRole('button', {name:'Copy SHA'}).click();
    await page.getByText('Copied.', {exact:true}).waitFor();
    await page.goto(base + '/settings/integrations/webhooks/new/');
    await page.locator('[name=name]').fill('Browser regression webhook');
    await page.locator('[name=product_id]').fill(String(account.product_id));
    await page.locator('[name=endpoint]').fill('https://consumer.example.com/events');
    await page.locator('[name=events][value="scan.completed"]').check();
    await page.locator('[name=enabled]').uncheck();
    await page.getByRole('button', {name:'Save webhook'}).click();
    await page.getByRole('heading', {name:'Save the signing secret'}).waitFor();
    const secret = await page.locator('#webhook-secret').inputValue();
    if (secret.length < 40) throw new Error('Signing secret not generated');
    await page.getByRole('link', {name:'Continue to delivery history'}).click();
    if ((await page.content()).includes(secret)) throw new Error('Secret persisted in history UI');
    await page.getByRole('link', {name:'Edit configuration'}).click();
    if ((await page.content()).includes(secret)) throw new Error('Secret leaked in edit UI');
    await page.locator('[name=endpoint]').fill('http://127.0.0.1/');
    await page.getByRole('button', {name:'Save webhook'}).click();
    await page.getByText('Use a public HTTPS endpoint', {exact:false}).waitFor();
    const report = {base,results,errors,workflow:'create / one-time secret / history / edit / unsafe endpoint rejection / Copy SHA',pass:errors.length===0 && results.every(r=>r.violations.length===0)};
    fs.writeFileSync(path.join(__dirname,'raw','browser.json'), JSON.stringify(report,null,2)+'\n');
    if (!report.pass) process.exitCode=1;
  } finally { await browser.close(); }
})().catch(error => { console.error(error.stack); process.exitCode=1; });
