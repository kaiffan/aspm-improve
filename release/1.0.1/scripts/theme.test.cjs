const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const source=fs.readFileSync('dojo/static/dojo/js/aspm.js','utf8');
function boot(saved, dark=false, blocked=false) {
 const observers=[],events={}, ready=[], media={matches:dark,addEventListener:(_,fn)=>media.changed=fn};
 const root={dataset:{},style:{},removeAttribute(){},hasAttribute(){return false;}};
 const storage={value:saved,getItem(){if(blocked)throw Error('blocked');return this.value;},setItem(_,v){if(blocked)throw Error('blocked');this.value=v;}};
 const window={matchMedia:()=>media,addEventListener:(n,fn)=>events[n]=fn,dispatchEvent:e=>{if(events[e.type])events[e.type](e);}};
 const document={documentElement:root,querySelectorAll:()=>[],getElementById:()=>null,addEventListener:(n,fn)=>{if(n==='DOMContentLoaded')ready.push(fn);}};
 vm.runInNewContext(source,{window,document,localStorage:storage,CustomEvent:class{constructor(type,init){this.type=type;this.detail=init.detail;}},MutationObserver:class{constructor(fn){observers.push(fn);}observe(){}},getComputedStyle:()=>({getPropertyValue:()=>''})});
 return {window,document,root,storage,media,events,ready,observers};
}
test('System is the default and applies before DOM ready',()=>{const s=boot(null,true);assert.equal(s.root.dataset.theme,'dark');assert.equal(s.root.dataset.themePreference,'system');});
test('Explicit light preference overrides dark system and persists',()=>{const s=boot('light',true);assert.equal(s.root.dataset.theme,'light');s.window.ASPMTheme.set('dark');assert.equal(s.storage.value,'dark');assert.equal(s.root.dataset.theme,'dark');});
test('System preference reacts to OS changes',()=>{const s=boot('system',false);s.media.matches=true;s.media.changed();assert.equal(s.root.dataset.theme,'dark');});
test('Explicit preference ignores OS changes',()=>{const s=boot('light',false);s.media.matches=true;s.media.changed();assert.equal(s.root.dataset.theme,'light');});
test('Disabled storage keeps theme controls functional',()=>{const s=boot(null,true,true);assert.equal(s.root.dataset.theme,'dark');s.window.ASPMTheme.set('light');assert.equal(s.root.dataset.theme,'light');});
test('Invalid stored or cross-tab values fall back to System',()=>{const s=boot('invalid',true);assert.equal(s.window.ASPMTheme.get(),'system');s.events.storage({key:'aspm.theme',newValue:'light'});assert.equal(s.root.dataset.theme,'light');});
test('Chart theming preserves scale/data behavior and disabled plugins',()=>{const s=boot(null);const fn=()=>42;const options={scales:{x:{type:'time',ticks:{callback:fn}}},plugins:{legend:false,tooltip:false}};s.window.ASPMTheme.styleChartOptions(options);assert.equal(options.scales.x.type,'time');assert.equal(options.scales.x.ticks.callback,fn);assert.equal(options.plugins.legend,false);assert.equal(options.plugins.tooltip,false);});
test('Chart theming does not assign resolved proxies back into their parents',()=>{const s=boot(null);function guarded(obj){return new Proxy(obj,{set(target,key,value){assert.notEqual(value,target[key],'existing nested object must retain its identity');target[key]=value;return true;}});}const labels={};const legend=guarded({labels});const plugins=guarded({legend,tooltip:{}});const opts=guarded({plugins,scales:{x:guarded({ticks:{},grid:{},border:{}})}});s.window.ASPMTheme.styleChartOptions(opts);assert.equal(opts.plugins,plugins);});

test('Tagulous replacement retains the visible form label',()=>{const s=boot(null);const label={htmlFor:'id_tags',id:''};const attrs={};const selection={closest:selector=>selector.includes('.form-group')?{querySelector:()=>label}:{previousElementSibling:{labels:[],id:''}},setAttribute:(k,v)=>attrs[k]=v};s.document.querySelectorAll=selector=>selector.includes("select2")?[selection]:[];s.events.load();assert.equal(attrs['aria-labelledby'],'id_tags-aspm-label');assert.equal(label.id,attrs['aria-labelledby']);});

test('Select2 inline search retains the native filter label',()=>{const s=boot(null),label={htmlFor:'id_product',id:''},attrs={};const search={closest:selector=>selector.includes('form-group')?null:{previousElementSibling:{labels:[label],id:'id_product'}},setAttribute:(k,v)=>attrs[k]=v};s.document.querySelectorAll=selector=>selector.includes('.select2-search__field')?[search]:[];s.events.load();assert.equal(attrs['aria-labelledby'],'id_product-aspm-label');});
test('Detached Select2 search gets a name without overwriting an explicit one',()=>{for(const existing of [null,'Search severity']){const s=boot(null),attrs=existing?{'aria-label':existing}:{},search={closest:()=>null,matches:()=>true,getAttribute:k=>attrs[k],setAttribute:(k,v)=>attrs[k]=v};s.document.querySelectorAll=selector=>selector.includes('.select2-search__field')?[search]:[];s.events.load();assert.equal(attrs['aria-label'],existing||'Search options');}});
test('Filters initialized after window load receive accessible names',()=>{const s=boot(null),attrs={},label={htmlFor:'id_severity',id:''},native={labels:[label],id:'id_severity'},selection={closest:selector=>selector.includes('form-group')?null:{previousElementSibling:native},setAttribute:(k,v)=>attrs[k]=v};let initialized=false;const group={querySelectorAll:()=>initialized?[selection]:[]};s.document.querySelectorAll=selector=>selector==='.filter-form-input'?[group]:[];s.events.load();assert.equal(s.observers.length,1);initialized=true;s.observers[0]();assert.equal(attrs['aria-labelledby'],'id_severity-aspm-label');});
