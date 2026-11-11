const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const source=fs.readFileSync('dojo/static/dojo/js/aspm.js','utf8');
function boot(saved, dark=false, blocked=false) {
 const events={}, ready=[], media={matches:dark,addEventListener:(_,fn)=>media.changed=fn};
 const root={dataset:{},style:{},removeAttribute(){},hasAttribute(){return false;}};
 const storage={value:saved,getItem(){if(blocked)throw Error('blocked');return this.value;},setItem(_,v){if(blocked)throw Error('blocked');this.value=v;}};
 const window={matchMedia:()=>media,addEventListener:(n,fn)=>events[n]=fn,dispatchEvent:e=>{if(events[e.type])events[e.type](e);}};
 const document={documentElement:root,querySelectorAll:()=>[],getElementById:()=>null,addEventListener:(n,fn)=>{if(n==='DOMContentLoaded')ready.push(fn);}};
 vm.runInNewContext(source,{window,document,localStorage:storage,CustomEvent:class{constructor(type,init){this.type=type;this.detail=init.detail;}},getComputedStyle:()=>({getPropertyValue:()=>''})});
 return {window,root,storage,media,events,ready};
}
test('System is the default and applies before DOM ready',()=>{const s=boot(null,true);assert.equal(s.root.dataset.theme,'dark');assert.equal(s.root.dataset.themePreference,'system');});
test('Explicit light preference overrides dark system and persists',()=>{const s=boot('light',true);assert.equal(s.root.dataset.theme,'light');s.window.ASPMTheme.set('dark');assert.equal(s.storage.value,'dark');assert.equal(s.root.dataset.theme,'dark');});
test('System preference reacts to OS changes',()=>{const s=boot('system',false);s.media.matches=true;s.media.changed();assert.equal(s.root.dataset.theme,'dark');});
test('Explicit preference ignores OS changes',()=>{const s=boot('light',false);s.media.matches=true;s.media.changed();assert.equal(s.root.dataset.theme,'light');});
test('Disabled storage keeps theme controls functional',()=>{const s=boot(null,true,true);assert.equal(s.root.dataset.theme,'dark');s.window.ASPMTheme.set('light');assert.equal(s.root.dataset.theme,'light');});
test('Invalid stored or cross-tab values fall back to System',()=>{const s=boot('invalid',true);assert.equal(s.window.ASPMTheme.get(),'system');s.events.storage({key:'aspm.theme',newValue:'light'});assert.equal(s.root.dataset.theme,'light');});
test('Chart theming preserves scale/data behavior and disabled plugins',()=>{const s=boot(null);const fn=()=>42;const options={scales:{x:{type:'time',ticks:{callback:fn}}},plugins:{legend:false,tooltip:false}};s.window.ASPMTheme.styleChartOptions(options);assert.equal(options.scales.x.type,'time');assert.equal(options.scales.x.ticks.callback,fn);assert.equal(options.plugins.legend,false);assert.equal(options.plugins.tooltip,false);});
test('Chart theming does not assign resolved proxies back into their parents',()=>{const s=boot(null);function guarded(obj){return new Proxy(obj,{set(target,key,value){assert.notEqual(value,target[key],'existing nested object must retain its identity');target[key]=value;return true;}});}const labels={};const legend=guarded({labels});const plugins=guarded({legend,tooltip:{}});const opts=guarded({plugins,scales:{x:guarded({ticks:{},grid:{},border:{}})}});s.window.ASPMTheme.styleChartOptions(opts);assert.equal(opts.plugins,plugins);});
