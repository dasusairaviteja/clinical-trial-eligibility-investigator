'use strict';
// DOM contract checks, not a substitute for browser/accessibility QA.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
class Element {
  constructor() {this.children=[];this.handlers={};this.value='';this.textContent='';}
  append(...nodes){this.children.push(...nodes);}
  replaceChildren(...nodes){this.children=nodes;}
  addEventListener(name,handler){this.handlers[name]=handler;}
}
const elements=new Map();
const element=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
let requests=[];
const context={document:{getElementById:element,createElement:()=>new Element()},
  fetch:async(path,options)=>{requests.push({path,options});return {ok:true,json:async()=>path==='/v1/me'?{reviewer:'signed-reviewer'}:{case_id:'synthetic'}};},
  Blob,URL};
vm.createContext(context);
vm.runInContext(fs.readFileSync('web/workspace.js','utf8'),context);
(async()=>{
  element('token').value='test-memory-token';
  await element('login').handlers.submit({preventDefault(){}});
  assert.equal(requests.find(r=>r.path==='/v1/me').options.headers.Authorization,'Bearer test-memory-token');
  assert.equal(element('token').value,'');
  assert.equal(element('reviewer').readOnly,true);
  vm.runInContext(`render({id:'r1',revision:1,report:{execution:{tool_calls:1},criteria:[{criterion_id:'c1',kind:'inclusion',statement:'Age rule',verdict:'unknown',review_signal:'needs_clarification',citations:[],missing_information:['Missing evidence']}]},audit:[{event:{action:'correction',criterion_id:'c1',verdict:'supported',reviewer:'signed-reviewer',reason:'Reviewed',at:'2026-10-06',revision:1}}]})`,context);
  assert(element('criteria').children[0].children.some(n=>n.textContent.includes('Latest reviewer assertion: supported')));
  element('logout').handlers.click();
  assert.equal(element('results').hidden,true);
  assert.equal(element('request').value,'');
  await vm.runInContext("api('/v1/me')",context);
  assert.equal(requests.at(-1).options.headers.Authorization,undefined);
  console.log('Workspace DOM contracts: token, reviewer correction and disconnect passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
