/* Real CSRF-protected login/create/edit. Only run on the copied RC database. */
const fs=require('node:fs');const assert=require('node:assert/strict');const {chromium}=require('playwright');
(async()=>{
 const a=JSON.parse(fs.readFileSync(process.env.ASPM_CREDENTIALS,'utf8'))[0];
 const test=JSON.parse(fs.readFileSync(process.env.ASPM_WRITE_CONTEXT,'utf8'));
 const login=JSON.parse(fs.readFileSync(process.env.ASPM_LOGIN_CREDENTIALS,'utf8'));
 const base='http://127.0.0.1:48086',out=[],browser=await chromium.launch({headless:true});
 async function check(name,fn){try{await fn();out.push({name,pass:true});}catch(e){out.push({name,pass:false,error:e.message.slice(0,500)});}}
 const context=await browser.newContext({viewport:{width:1440,height:1000}});await context.addCookies([{name:'sessionid',value:a.session,domain:'127.0.0.1',path:'/',httpOnly:true,sameSite:'Lax'}]);const p=await context.newPage();let finding=test.finding;
 await check('Create finding through browser form',async()=>{
  if(finding){const r=await p.request.get(base+'/api/v2/findings/'+finding+'/',{headers:{Authorization:'Token '+a.token}});assert.equal(r.status(),200);assert.ok((await r.json()).title.toLowerCase().startsWith('aspm rc1 browser validation'));return;}
  await p.goto(base+'/test/'+test.test+'/add_findings',{waitUntil:'networkidle'});
  await p.locator('#id_title').fill('ASPM RC1 browser validation');await p.locator('#id_date').fill('2026-11-11');await p.locator('#id_severity').selectOption('Low');
  await p.locator('.CodeMirror').first().evaluate(el=>el.CodeMirror.setValue('Isolated release smoke finding. Synthetic test evidence only.'));
  await p.locator('#id_vulnerability_ids').fill('CVE-2026-99991\nGHSA-2345-6789-cfgh');
  await Promise.all([p.waitForURL(base+'/test/'+test.test),p.locator('input[name="_Finished"]').click()]);
  const response=await p.request.get(base+'/api/v2/findings/?test='+test.test+'&title='+encodeURIComponent('ASPM RC1 browser validation'),{headers:{Authorization:'Token '+a.token}});
  const payload=await response.json();assert.equal(payload.count,1);finding=payload.results[0].id;assert.ok(finding);await p.goto(base+'/finding/'+finding,{waitUntil:'networkidle'});await p.screenshot({path:'release/1.0.1/screenshots/aspm-created-finding.png'});
 });
 if(finding)await check('Edit finding through browser form',async()=>{
  await p.goto(base+'/finding/'+finding+'/edit',{waitUntil:'networkidle'});const previous=await p.locator('#id_title').inputValue();const desired='ASPM RC1 browser validation '+(previous.toLowerCase().endsWith('edited')?'reviewed':'edited');await p.locator('#id_title').fill(desired);
  await Promise.all([p.waitForURL(/\/finding\/\d+$/),p.locator('form#add_finding input[type=submit], form#add_finding button[type=submit]').first().click()]);
  const response=await p.request.get(base+'/api/v2/findings/'+finding+'/',{headers:{Authorization:'Token '+a.token}});const data=await response.json();assert.equal(data.title.toLowerCase(),desired.toLowerCase());assert.notEqual(data.title.toLowerCase(),previous.toLowerCase());await p.screenshot({path:'release/1.0.1/screenshots/aspm-created-finding.png'});
 });
 await context.close();
 const anon=await browser.newContext({viewport:{width:1440,height:1000}});const page=await anon.newPage();
 await check('Login rejects invalid password',async()=>{await page.goto(base+'/login?force_login_form',{waitUntil:'networkidle'});await page.locator('input[name=username]').fill(login.username);await page.locator('input[name=password]').fill('invalid-password-for-release-check');await Promise.all([page.waitForNavigation(),page.locator('form button[type=submit],form input[type=submit]').first().click()]);assert.ok(await page.locator('input[type=password]').count());});
 await check('Login accepts isolated test account',async()=>{await page.locator('input[name=password]').fill(login.password);await Promise.all([page.waitForNavigation(),page.locator('form button[type=submit],form input[type=submit]').first().click()]);assert.ok(!new URL(page.url()).pathname.startsWith('/login'));});
 await check('Access-free account cannot read foreign finding',async()=>{const r=await page.goto(base+'/finding/'+a.finding,{waitUntil:'networkidle'});assert.equal(r.status(),400);assert.ok((await page.locator('body').innerText()).includes('403 Forbidden'));assert.ok(!(await page.locator('body').innerText()).includes('Get Pro'));const api=await page.request.get(base+'/api/v2/findings/'+a.finding+'/',{headers:{Authorization:'Token '+login.token}});assert.ok([403,404].includes(api.status()));const list=await page.request.get(base+'/api/v2/findings/',{headers:{Authorization:'Token '+login.token}});assert.equal((await list.json()).count,0);});
 await anon.close();await browser.close();
 fs.writeFileSync('release/1.0.1/measurements/browser-write-checks.json',JSON.stringify({finding,checks:out},null,2)+'\n');console.log(out.map(x=>({name:x.name,pass:x.pass,error:x.error})));if(out.some(x=>!x.pass))process.exitCode=1;
})().catch(e=>{console.error(e.message);process.exitCode=1;});
