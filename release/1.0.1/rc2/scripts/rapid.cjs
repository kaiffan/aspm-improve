/* Rapid sequential navigation preserves filters, page contents and selected theme. */
const fs=require('node:fs'),assert=require('node:assert/strict'),{chromium}=require('playwright');
(async()=>{
 const account=JSON.parse(fs.readFileSync(process.env.ASPM_CREDENTIALS))[0],base=process.env.ASPM_URL,browser=await chromium.launch(),rows=[];
 for(const width of [1440,390])for(const mode of ['light','dark','system']){
  const c=await browser.newContext({viewport:{width,height:900},colorScheme:'light'});
  await c.addInitScript(value=>localStorage.setItem('aspm.theme',value),mode);
  await c.addCookies([{name:'sessionid',value:account.session,domain:'127.0.0.1',path:'/',httpOnly:true,sameSite:'Lax'}]);
  const page=await c.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message.slice(0,200)));
  const r=await page.goto(base+`/finding/open?test__engagement__product=${account.product}&severity=High`,{waitUntil:'networkidle'});assert.equal(r.status(),200);
  await page.locator('button.toggle-filters').first().click();
  await page.waitForSelector('.filter-form-input .select2-selection[role="combobox"]');
  const widgets=await page.locator('.filter-form-input .select2-selection[role="combobox"]').count();assert.ok(widgets>0);
  const ids=()=>page.locator('input.select_one').evaluateAll(es=>es.map(x=>x.id));
  const first=await ids();let second;
  for(const [label,expected]of [['Next',2],['Next',3],['Prev',2],['Prev',1]]){
   await Promise.all([page.waitForNavigation({waitUntil:'domcontentloaded'}),page.locator('.pagination a').filter({hasText:label}).first().click()]);
   const params=new URL(page.url()).searchParams;
   assert.equal(params.get('page'),String(expected));assert.equal(params.get('test__engagement__product'),String(account.product));assert.equal(params.get('severity'),'High');
   assert.equal(await page.locator('html').getAttribute('data-theme'),mode==='dark'?'dark':'light');
   const current=await ids();if(expected===2&&!second){second=current;assert.deepEqual(current.filter(x=>first.includes(x)),[]);}else if(expected===2)assert.deepEqual(current,second);else if(expected===1)assert.deepEqual(current,first);
  }
  assert.deepEqual(errors,[]);rows.push({viewport:width,mode,navigations:4,generated_comboboxes:widgets,filters_preserved:true,contents_stable:true,console_errors:errors,pass:true});await c.close();
 }
 await browser.close();fs.writeFileSync('release/1.0.1/rc2/raw/browser-rapid.json',JSON.stringify({states:rows.length,navigations:rows.reduce((s,x)=>s+x.navigations,0),rows},null,2)+'\n');console.log('Rapid navigation passed:',rows.length,'states');
})().catch(e=>{console.error(e.message);process.exitCode=1;});
