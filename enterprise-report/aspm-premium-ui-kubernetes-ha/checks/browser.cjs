const assert = require('node:assert/strict');
const fs = require('node:fs');
const {chromium} = require('playwright');
const [out, loginFile, accountsFile] = process.argv.slice(2);
const [origin,user,password] = fs.readFileSync(loginFile,'utf8').trim().split('\n');
const base = new URL(origin).origin;
const widths = [320,360,390,768,1024,1280,1440,1920];
const spaces = {overview:'/dashboard',projects:'/workspace/projects',classic:'/workspace/classic',findings:'/finding',reports:'/workspace/reports',engagements:'/engagement/all'};
const mask = page => page.locator('input[name*=secret][value]:not([value=""]), input[name*=token][value]:not([value=""]), textarea[name*=secret]');
const data = {pages:[],actions:[],roles:[],contrast:[],errors:[]};
async function load(page, base, label, route, width, theme) {
  const res = await page.goto(base+route,{waitUntil:'domcontentloaded'});
  await page.evaluate(value=>window.ASPMTheme?.set(value),theme);
  const row = await page.evaluate(() => ({
    path:location.pathname, overflow:document.documentElement.scrollWidth-innerWidth,
    theme:document.documentElement.dataset.theme,
    source:[...document.querySelectorAll('link[rel=stylesheet]')].find(e=>e.href.includes('aspm.css'))?.href.split('v=')[1],
    outside:[...document.querySelectorAll('main *,#base-content *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1 && !e.closest('.table-responsive,[hidden]') && e.getClientRects().length).slice(0,8).map(e=>e.tagName+'.'+(typeof e.className==='string'?e.className:''))
  }));
  data.pages.push({label,width,status:res.status(),...row});
}
async function png(page, label) {
  await page.screenshot({path:out+'/screenshots/after-'+label+'.png',animations:'disabled',mask:[mask(page)]});
}
async function href(page, prefix, pattern) {
  return page.locator(prefix+' a[href]').evaluateAll((links, expression)=>links.map(a=>a.getAttribute('href')).find(p=>p && new RegExp(expression).test(p)),pattern);
}
(async()=>{
  const browser = await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--no-sandbox','--host-resolver-rules=MAP aspm-keycloak.test 127.0.0.1','--no-proxy-server']});
  try {
    await Promise.all([
      (async()=>{
        const page = await browser.newPage({ignoreHTTPSErrors:true,viewport:{width:1440,height:1000}});
        await page.goto(base+'/login');
        await png(page,'login-1440');
        await page.locator('#id_username').fill(user);
        await page.locator('#id_password').fill(password);
        await page.locator('#id_password').press('Enter');
        await page.waitForURL(u=>!u.pathname.startsWith('/login'));
        await page.goto(base+spaces.projects);
        const repoList = await href(page,'.aspm-project-list','^/product/[0-9]+/repositories/?$');
        if (repoList) {
          spaces.repositories=repoList;
          await page.goto(base+repoList);
          const repo = await href(page,'#base-content','^/repositories/[0-9]+/?$');
          if (repo) {
            spaces.commits=repo;
            await page.goto(base+repo);
            const commit = await href(page,'#base-content','^/commits/[0-9]+/?$');
            if (commit) {
              spaces.commit=commit.replace(/\/$/,'')+'/evidence';
              spaces['commit-scanner']=spaces.commit+'?tab=originals';
              spaces['commit-changes']=spaces.commit+'?tab=changes';
              await page.goto(base+spaces['commit-scanner']);
              spaces.test = await href(page,'#base-content','^/test/[0-9]+/?$');
              spaces.engagement = await href(page,'#base-content','^/engagement/[0-9]+/?$');
            }
          }
        }
        for (const width of widths) {
          await page.setViewportSize({width,height:width<768?844:1000});
          for (const theme of ['light','dark']) {
            for (const [label,route] of Object.entries(spaces)) {
              if (!route) continue;
              await load(page,base,label,route,width,theme);
              if ((width===1440&&theme==='light')||(width===320&&theme==='light')||(width===390&&theme==='dark'&&['findings','commit'].includes(label))) await png(page,label+'-'+width+(theme==='dark'?'-dark':''));
            }
          }
          await page.goto(base+spaces.projects);
          const toggle=page.locator('#aspm-nav-toggle');
          await toggle.click();
          if (width<1024) {
            assert.equal(await toggle.getAttribute('aria-expanded'),'true');
            assert.equal(await page.getByRole('dialog',{name:/navigation|навигац/i}).count(),1);
            assert.equal(await page.locator('#wrapper').evaluate(el=>el.inert),true);
            if (width===390) await png(page,'mobile-navigation-390');
            await page.keyboard.press('Escape');
            assert.equal(await toggle.getAttribute('aria-expanded'),'false');
            assert.equal(await toggle.evaluate(el=>el===document.activeElement),true);
          } else {
            await page.reload();
            assert.equal(await toggle.getAttribute('aria-expanded'),'false');
            const nav = page.locator('#dd-sidebar .aspm-nav-link[aria-current]');
            assert.equal(await nav.isVisible(),true);
            assert.ok((await page.locator('#dd-sidebar').boundingBox()).width<80);
            if (width===1440) await png(page,'compact-navigation-1440');
            await toggle.click();
          }
          data.actions.push({width,action:width<1024?'mobile dialog opens, focus contained, Escape restores focus':'desktop compact width, active link visibility and persistence',pass:true});
          await page.goto(base+spaces.findings);
          await page.locator('#show-filters').click();
          await page.locator('#the-filters').waitFor({state:'visible'});
          data.actions.push({width,action:'Findings disclosure',pass:true,overflow:await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)});
          const engagement = await page.goto(base+spaces.engagements);
          assert.ok(engagement.ok(), `Engagement list HTTP ${engagement.status()} at ${width}px`);
          const control = page.locator('#show-filters');
          const point = await control.evaluate(element => {
            const bounds = element.getBoundingClientRect();
            const x = bounds.x + bounds.width / 2, y = bounds.y + bounds.height / 2;
            if (!element.contains(document.elementFromPoint(x, y))) throw new Error('Engagement filter is obscured');
            return {x, y};
          });
          await page.mouse.click(point.x, point.y);
          await page.locator('#the-filters').waitFor({state:'visible'});
          data.actions.push({width,action:'Engagements disclosure via pointer hit test',pass:true,overflow:await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)});

        }
        await page.goto(base+spaces.engagements);
        await page.locator('#show-filters').press('Space');
        await page.locator('#the-filters').waitFor({state:'visible',timeout:6000});
        data.actions.push({action:'Engagements filter opens from the keyboard',pass:true});
        for (const theme of ['light','dark']) {
          await page.evaluate(value=>window.ASPMTheme.set(value),theme);
          const rows=await page.evaluate(()=>{
            const styles=getComputedStyle(document.documentElement);
            const luminance=token=>{
              const color=styles.getPropertyValue(token).trim();
              const channels=color.slice(1).match(/../g).map(x=>parseInt(x,16)/255)
                .map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);
              return channels[0]*.2126+channels[1]*.7152+channels[2]*.0722;
            };
            return [
              ['Text','--color-text','--color-surface',4.5],
              ['Muted text','--color-text-muted','--color-surface',4.5],
              ['Sidebar text','--aspm-sidebar-fg','--aspm-sidebar-bg',4.5],
              ['Selected navigation','--aspm-ink','--aspm-lime',4.5],
              ['Focus','--aspm-focus','--color-surface',3]
            ].map(([label,text,background,target])=>{
              const a=luminance(text), b=luminance(background);
              return {label,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05),target};
            });
          });
          data.contrast.push({theme,rows});
          assert.ok(rows.every(row=>row.ratio>=row.target),'Default contrast on '+theme);
        }
        if (spaces.commits) {
          await page.goto(base+spaces.commits);
          await page.locator('#repository-branch').fill('no-such-lab-branch');
          await page.locator('#repository-branch').press('Enter');
          await page.getByText('No linked commits match this branch.',{exact:true}).waitFor();
          data.actions.push({action:'Repository branch filter and empty state',pass:true});
        }
        if (spaces.commit) {
          await page.goto(base+spaces.commit+'?tab=originals');
          const original = page.locator('#base-content a[href*="/artifact/"]').first();
          const artifact = await page.request.get(base+await original.getAttribute('href'));
          assert.equal(artifact.status(),200);
          assert.match(artifact.headers()['content-disposition'],/attachment/);
          data.actions.push({action:'Scanner artifact download through TLS',pass:true});
        }
        await page.close();
      })().catch(error=>data.errors.push({area:'orb',message:error.message.split('\n').slice(0,8).join(' ')})),
      (async()=>{
        const accounts = JSON.parse(fs.readFileSync(accountsFile)).accounts;
        const keycloak = 'https://localhost:48141';
        await Promise.all(['secops','expert','reader-test','reader-payments','reader-both','reader-none'].map(async role=>{
          const c = await browser.newContext({ignoreHTTPSErrors:true,viewport:{width:390,height:844}});
          try {
            const page = await c.newPage();
            await page.goto(keycloak+'/sso/login');
            await page.locator('#username').fill(role);
            await page.locator('#password').fill(accounts[role].password);
            await page.locator('#kc-login').click();
            await page.waitForURL(u=>u.origin===keycloak && /workspace|dashboard/.test(u.pathname));
            const row = {role,projects:0,links:[],statuses:{}};
            for (const [label,route] of Object.entries({projects:spaces.projects,classic:spaces.classic,reports:spaces.reports})) {
              const res=await page.goto(keycloak+route);
              row.statuses[label]=res.status();
              if (label==='projects') {
                const products = page.locator('.aspm-project-list tbody th a');
                row.projects=await products.count();
                row.portfolio = await products.allTextContents();
                row.links=await page.locator('.aspm-nav-link').allTextContents();
                await png(page,role+'-390');
                if (row.projects) {
                  await products.first().click();
                  row.statuses.repositories = (await c.request.get(page.url())).status();
                }
              }
            }
            row.statuses.settings=(await c.request.get(keycloak+'/system_settings')).status();
            row.statuses.findings=(await c.request.get(keycloak+'/finding')).status();
            assert.equal(row.statuses.settings,role==='secops'?200:403);
            assert.equal(row.statuses.findings,role.startsWith('reader-')?403:200);
            if (role==='reader-none') assert.equal(row.projects,0);
            if (role==='reader-both') assert.ok(row.projects>=2);
            if (role.startsWith('reader-') && role!=='reader-none') assert.ok(row.projects>0);
            data.roles.push(row);
          } catch(error) { data.errors.push({role,message:error.message.split('\n')[0]}); }
          finally { await c.close(); }
        }));
      })()
    ]);
  } finally {
    await browser.close();
    fs.writeFileSync(out+'/raw/browser-after.json',JSON.stringify(data,null,2)+'\n');
  }
  console.log(JSON.stringify({pages:data.pages.length,actions:data.actions.length,roles:data.roles.length,errors:data.errors,overflow:data.pages.filter(x=>x.overflow>1).map(({label,width,theme,overflow})=>({label,width,theme,overflow}))}));
  if (data.errors.length) process.exitCode=1;
})().catch(error=>{console.error(error.message);process.exitCode=1});
