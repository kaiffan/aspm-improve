/* Test the real late-initialized Select2 widgets and navigation; no runtime mocking. */
const fs=require('node:fs'),assert=require('node:assert/strict'),{chromium}=require('playwright');
(async()=>{
 const account=JSON.parse(fs.readFileSync(process.env.ASPM_CREDENTIALS))[0],base=process.env.ASPM_URL;
 const browser=await chromium.launch(),rows=[];
 for(const width of [1440,390]){
  const context=await browser.newContext({viewport:{width,height:width===390?844:1000}});
  await context.addInitScript(()=>localStorage.setItem('aspm.theme','dark'));
  await context.addCookies([{name:'sessionid',value:account.session,domain:'127.0.0.1',path:'/',httpOnly:true,sameSite:'Lax'}]);
  const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message.slice(0,200)));
  const r=await page.goto(base+`/finding/open?test__engagement__product=${account.product}&severity=High&active=2`,{waitUntil:'networkidle'});assert.equal(r.status(),200);
  await page.locator('button.toggle-filters').first().click();
  await page.waitForSelector('.filter-form-input .select2-selection[role="combobox"]');
  const controls=await page.locator('.filter-form-input .select2-selection[role="combobox"]').count();assert.ok(controls>0);
  await page.evaluate(fs.readFileSync(require.resolve('axe-core/axe.min.js'),'utf8'));
  const violations=await page.evaluate(async()=>{const result=await window.axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});return result.violations.map(x=>({id:x.id,count:x.nodes.length,targets:x.nodes.map(n=>n.target)}));});
  await page.screenshot({path:`release/1.0.1/rc2/screenshots/expanded-${width}-dark.png`});
  assert.deepEqual(violations,[]);assert.deepEqual(errors,[]);
  await Promise.all([page.waitForNavigation(),page.locator('th a[href*="o=title"]').first().click()]);
  assert.equal(new URL(page.url()).searchParams.get('o'),'title');
  await Promise.all([page.waitForNavigation(),page.locator('.pagination a').filter({hasText:'Next'}).first().click()]);
  assert.equal(new URL(page.url()).searchParams.get('test__engagement__product'),String(account.product));
  assert.equal(new URL(page.url()).searchParams.get('severity'),'High');
  await page.locator('#pageSizeDropdown').first().click();
  await Promise.all([page.waitForNavigation(),page.getByRole('menuitem',{name:'50 items per page',exact:true}).first().click()]);
  assert.equal(new URL(page.url()).searchParams.get('page_size'),'50');
  for(const mode of ['light','system','dark'])await page.locator('[data-theme-control]').selectOption(mode);
  await page.locator('button.toggle-filters').first().click();
  await Promise.all([page.waitForNavigation(),page.locator('a#clear').first().click()]);
  assert.equal(new URL(page.url()).search,'');
  rows.push({viewport:width,status:200,generated_comboboxes:controls,axe:violations,console_errors:errors,navigation:['sort','next','size_50','light','system','dark','clear'],pass:true});
  await context.close();
 }
 await browser.close();fs.writeFileSync('release/1.0.1/rc2/raw/browser-expanded.json',JSON.stringify({rows,passed:rows.length},null,2)+'\n');console.log('Expanded dark filters and navigation passed:',rows.length);
})().catch(e=>{console.error(e.message);process.exitCode=1;});
