/* Read-only release checks. Credentials and sessions remain outside artifacts. */
const fs = require('node:fs');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const root='release/1.0.1';
(async()=>{
 const a=JSON.parse(fs.readFileSync(process.env.ASPM_CREDENTIALS,'utf8'))[0];
 const base=process.env.ASPM_URL||'http://127.0.0.1:48086';
 const browser=await chromium.launch({headless:true});
 const rows=[],checks=[],failures=[];
 const paths=[['dashboard','/dashboard'],['findings','/finding/open'],['finding','/finding/'+a.finding],['products','/asset'],['product','/asset/'+a.product],['engagements','/engagement'],['engagement','/engagement/'+a.engagement],['test','/test/'+a.test],['reports','/reports/builder'],['finding-new','/test/'+a.test+'/add_findings'],['finding-edit','/finding/'+a.finding+'/edit'],['support','/support']];
 const check=async(name,fn)=>{try{await fn();checks.push({name,pass:true});}catch(e){checks.push({name,pass:false,error:e.message.slice(0,300)});failures.push(name);}};
 for(const viewport of [{width:1440,height:1000},{width:390,height:844}])for(const mode of ['light','dark']){
  const context=await browser.newContext({viewport,colorScheme:'light'});
  await context.addInitScript(value=>localStorage.setItem('aspm.theme',value),mode);
  await context.addCookies([{name:'sessionid',value:a.session,domain:'127.0.0.1',path:'/',httpOnly:true,sameSite:'Lax'}]);
  const page=await context.newPage();let errors=[],failed=[];
  page.on('pageerror',e=>errors.push(e.message.slice(0,250)));
  page.on('response',r=>{if(r.status()>=400)failed.push({path:new URL(r.url()).pathname,status:r.status()});});
  for(const [name,path]of paths){
   const response=await page.goto(base+path,{waitUntil:'networkidle',timeout:90000});
   console.log('PAGE',name,mode,viewport.width,response.status());
   const size=viewport.width>1000?'desktop':'mobile';
   await page.screenshot({path:`${root}/screenshots/aspm-${name}-${size}-${mode}.png`});
   await page.evaluate(fs.readFileSync(require.resolve('axe-core/axe.min.js'),'utf8'));
   const axe=await page.evaluate(async()=>{const r=await window.axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}});return r.violations.map(v=>({id:v.id,impact:v.impact,count:v.nodes.length,nodes:v.nodes.slice(0,5).map(n=>({target:n.target,summary:n.failureSummary}))}));});
   const row={name,mode,viewport:viewport.width,status:response.status(),path:new URL(page.url()).pathname,theme:await page.locator('html').getAttribute('data-theme'),lang:await page.locator('html').getAttribute('lang'),overflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),errors,failed,axe};
   rows.push(row);errors=[];failed=[];
   if(row.status!==200||row.errors.length||row.failed.length||row.overflow||row.axe.length)failures.push(`${name}-${size}-${mode}`);
   if(name==='dashboard'){
    await check(`theme switch ${size} ${mode}`,async()=>{await page.locator('[data-theme-control]').selectOption('dark');assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');await page.locator('[data-theme-control]').selectOption('light');assert.equal(await page.locator('html').getAttribute('data-theme'),'light');await page.locator('[data-theme-control]').selectOption('system');await page.emulateMedia({colorScheme:'dark'});await page.waitForFunction(()=>document.documentElement.dataset.theme==='dark');assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');await page.emulateMedia({colorScheme:'light'});await page.waitForFunction(()=>document.documentElement.dataset.theme==='light');assert.equal(await page.locator('html').getAttribute('data-theme'),'light');await page.locator('[data-theme-control]').selectOption(mode);});
    if(size==='mobile')await check(`sidebar keyboard ${mode}`,async()=>{await page.locator('#aspm-nav-toggle').click();assert.equal(await page.locator('#aspm-nav-toggle').getAttribute('aria-expanded'),'true');await page.keyboard.press('Escape');assert.equal(await page.locator('#aspm-nav-toggle').getAttribute('aria-expanded'),'false');assert.equal(await page.evaluate(()=>document.activeElement.id),'aspm-nav-toggle');});
   }
   if(name==='findings')await check(`selection ${size} ${mode}`,async()=>{await page.locator('#select_all').check();await page.waitForFunction(()=>document.querySelectorAll('input.select_one:checked').length>0);await page.locator('#select_all').uncheck();});
  }
  await context.close();
 }
 // A genuinely anonymous context, separate from the authenticated workspace.
 for(const mode of ['light','dark']){
  const context=await browser.newContext({viewport:{width:390,height:844},colorScheme:mode});const page=await context.newPage();const r=await page.goto(base+'/login?force_login_form',{waitUntil:'networkidle'});await page.screenshot({path:`${root}/screenshots/aspm-login-mobile-${mode}.png`});
  rows.push({name:'login',mode,viewport:390,status:r.status(),path:new URL(page.url()).pathname,theme:await page.locator('html').getAttribute('data-theme'),overflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)});
  await check('anonymous login '+mode,async()=>{assert.equal(r.status(),200);assert.ok(await page.locator('input[type=password]').count());assert.equal(await page.locator('html').getAttribute('data-theme'),mode);});await context.close();
 }
 await browser.close();
 fs.writeFileSync(`${root}/measurements/browser-validation.json`,JSON.stringify({rows,checks,failures},null,2)+'\n');
 console.log(JSON.stringify({pages:rows.length,checks:checks.length,failures,axe:rows.filter(r=>r.axe?.length).map(r=>({name:r.name,mode:r.mode,viewport:r.viewport,issues:r.axe.map(v=>[v.id,v.count])}))}));
 if(failures.length)process.exitCode=1;
})().catch(e=>{console.error(e.message);process.exitCode=1;});
