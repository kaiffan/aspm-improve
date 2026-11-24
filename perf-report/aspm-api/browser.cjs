const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.ASPM_PLAYWRIGHT_MODULE || 'playwright');
(async () => {
 const credentials = JSON.parse(fs.readFileSync(process.env.ASPM_CREDENTIALS, 'utf8'));
 const http = JSON.parse(fs.readFileSync('perf-report/aspm-api/http.json', 'utf8'));
 const base = process.env.ASPM_BASE_URL || 'http://127.0.0.1:48094';
 const root = 'perf-report/aspm-api';
 fs.mkdirSync(path.join(root, 'screenshots'), { recursive: true });
 const browser = await chromium.launch({headless:true, executablePath:process.env.ASPM_CHROMIUM});
 const rows = [];
 for (const width of [1440,390]) for (const theme of ['light','dark']) {
  const context = await browser.newContext({viewport:{width,height:1000}});
  await context.addInitScript(value=>localStorage.setItem('aspm.theme',value),theme);
  await context.addCookies([{name:'sessionid',value:credentials.session,domain:'127.0.0.1',path:'/',httpOnly:true,sameSite:'Lax'}]);
  const page = await context.newPage();
  let errors=[];
  page.on('pageerror',e=>errors.push(e.message.slice(0,250)));
  const repositoriesResponse = await context.request.get(base+`/api/aspm/v1/projects/${credentials.product_id}/repositories/`);
  assert.equal(repositoriesResponse.status(),200);
  const repositories = await repositoriesResponse.json();
  const repository = repositories.find(row=>row.url===http.repository_url);
  const pages = [
   ['project',`/asset/${credentials.product_id}`],
   ['repositories',`/product/${credentials.product_id}/repositories`],
   ['commits',`/repositories/${repository.id}`],
   ['commit',`/commits/${http.commit_id}`],
   ['new-engagement',`/asset/${credentials.product_id}/new_engagement`],
   ['new-cicd-engagement',`/asset/${credentials.product_id}/new_engagement/cicd`],
   ...['overview','originals','reports','findings','changes'].map(tab=>[tab,`/commits/${http.commit_id}/evidence?tab=${tab}`]),
  ];
  for (const [name,url] of pages) {
   errors=[];
   const response = await page.goto(base+url,{waitUntil:'networkidle',timeout:60000});
   assert.equal(response.status(),200,`${name} HTTP status`);
   if(name==='project') assert.equal(await page.getByTestId('product-tab-repositories').count(),1);
   assert.equal(await page.locator('input[type=file]').count(),0);
   assert.equal(await page.locator('form[enctype="multipart/form-data"]').count(),0);
   assert.equal(await page.getByRole('link',{name:/Upload Scan|Import Scan Results|Re-Upload Scan/i}).count(),0);
   assert.equal(await page.getByRole('button',{name:/Upload Scan|Import Scan Results|Re-Upload Scan/i}).count(),0);
   const overflow = await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
   rows.push({name,width,theme,status:response.status(),overflow,errors:[...errors]});
   await page.screenshot({path:path.join(root,'screenshots',`${name}-${width}-${theme}.png`),fullPage:true});
   assert.equal(overflow,false,`${name} viewport overflow at ${width}`);
   assert.deepEqual(errors,[],`${name} JavaScript errors`);
  }
  await page.goto(base+`/commits/${http.commit_id}/evidence?tab=reports`,{waitUntil:'networkidle'});
  const downloadEvent = page.waitForEvent('download');
  await page.getByRole('link',{name:'JSON',exact:true}).first().click();
  const download = await downloadEvent;
  const generated = JSON.parse(fs.readFileSync(await download.path(),'utf8'));
  assert.equal(generated.report.commit_sha,'c'.repeat(40));
  assert.equal(generated.report.complete,true);
  await context.close();
 }
 await browser.close();
 fs.writeFileSync(path.join(root,'browser.json'),JSON.stringify({pages:rows.length,rows,checks:{no_upload_controls:true,read_only_navigation:true,downloads:true}},null,2)+'\n');
 console.log(JSON.stringify({pages:rows.length,errors:rows.flatMap(row=>row.errors),overflow:rows.filter(row=>row.overflow).length}));
})().catch(error=>{console.error(error.message);process.exitCode=1;});
