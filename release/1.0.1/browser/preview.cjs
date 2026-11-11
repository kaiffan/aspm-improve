const fs=require('node:fs');
const {chromium}=require('playwright');
(async()=>{
 const accounts=JSON.parse(fs.readFileSync(process.env.ASPM_CREDENTIALS,'utf8'));const a=accounts[0];
 const browser=await chromium.launch({headless:true});let results=[];
 for(const mode of ['light','dark']){
  const context=await browser.newContext({viewport:{width:1440,height:1000},colorScheme:'light'});
  await context.addInitScript(value=>localStorage.setItem('aspm.theme',value),mode);
  await context.addCookies([{name:'sessionid',value:a.session,domain:'127.0.0.1',path:'/',httpOnly:true,sameSite:'Lax',secure:false}]);
  const page=await context.newPage();let errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(const [name,path]of[['dashboard','/dashboard'],['findings','/finding/open'],['products','/asset'],['test','/test/'+a.test],['login','/login?force_login_form']]){
   const resp=await page.goto((process.env.ASPM_URL||'http://127.0.0.1:48086')+path,{waitUntil:'networkidle',timeout:90000});
   await page.screenshot({path:`release/1.0.1/screenshots/aspm-${name}-desktop-${mode}.png`});
   results.push({name,mode,status:resp.status(),url:page.url(),title:await page.title(),theme:await page.locator('html').getAttribute('data-theme'),overflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),errors:[...errors]});errors=[];
  }
  await context.close();
 }
 await browser.close();fs.writeFileSync('release/1.0.1/measurements/browser-preview.json',JSON.stringify(results,null,2)+'\n');console.log(results);
})().catch(e=>{console.error(e.message);process.exitCode=1;});
