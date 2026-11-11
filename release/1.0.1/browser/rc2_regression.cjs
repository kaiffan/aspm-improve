/* Read-only live browser regression. Secrets are read from a private credential file. */
const fs=require('node:fs'),assert=require('node:assert/strict'),{chromium}=require('playwright');
(async()=>{
 const a=JSON.parse(fs.readFileSync(process.env.ASPM_CREDENTIALS))[0],base=process.env.ASPM_URL||'http://127.0.0.1:48091';
 const out=process.env.ASPM_OUTPUT||'release/1.0.1/rc2/raw/browser-before.json', rows=[],b=await chromium.launch();
 const c=await b.newContext({viewport:{width:1440,height:1000}});await c.addCookies([{name:'sessionid',value:a.session,domain:'127.0.0.1',path:'/',httpOnly:true,sameSite:'Lax'}]);const p=await c.newPage();
 async function check(name,fn){try{rows.push({name,pass:true,...await fn()});}catch(e){rows.push({name,pass:false,error:e.message.slice(0,400)});}}
 const ids=()=>p.locator('input.select_one').evaluateAll(es=>es.map(e=>e.id));
 await check('Product + severity filter applies and survives next page',async()=>{
  await p.goto(base+`/finding/open?test__engagement__product=${a.product}&severity=High`,{waitUntil:'networkidle'});
  assert.equal(await p.locator('select[name=test__engagement__product]').first().inputValue(),String(a.product));
  assert.ok((await ids()).length>0);await Promise.all([p.waitForNavigation(),p.locator('.pagination a').filter({hasText:'Next'}).first().click()]);
  assert.equal(new URL(p.url()).searchParams.get('test__engagement__product'),String(a.product));assert.equal(new URL(p.url()).searchParams.get('severity'),'High');
 });
 await check('Clear removes applied Product and severity from URL/results',async()=>{
  await p.goto(base+`/finding/open?test__engagement__product=${a.product}&severity=High`,{waitUntil:'networkidle'});
  await p.locator('button.toggle-filters').first().click();await p.locator('a#clear').first().click();await p.waitForTimeout(1500);
  assert.equal(new URL(p.url()).search,'');
 });
 await check('Default severity order has no overlap between first and next page',async()=>{
  await p.goto(base+'/finding/open?severity=High',{waitUntil:'networkidle'});const first=await ids();
  await Promise.all([p.waitForNavigation(),p.locator('.pagination a').filter({hasText:'Next'}).first().click()]);const second=await ids();
  const overlap=second.filter(x=>first.includes(x));assert.deepEqual(overlap,[]);return{first_count:first.length,next_count:second.length};
 });
 await check('Malformed page_size returns a usable page',async()=>{const r=await p.goto(base+'/finding/open?page_size=bad',{waitUntil:'networkidle'});assert.equal(r.status(),200);assert.equal((await ids()).length,25);});
 await p.screenshot({path:out.replace('.json','.png')});await b.close();fs.writeFileSync(out,JSON.stringify(rows,null,2)+'\n');console.log(JSON.stringify(rows));if(rows.some(r=>!r.pass))process.exitCode=1;
})().catch(e=>{console.error(e.message);process.exitCode=1;});
