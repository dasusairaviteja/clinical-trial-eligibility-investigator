'use strict';
const el = id => document.getElementById(id);
let current = null;
let accessToken = '';
async function api(path, body) {
  const headers = accessToken ? {Authorization:'Bearer '+accessToken} : {};
  if(body !== undefined) headers['Content-Type']='application/json';
  const response = await fetch(path, {method:body === undefined ? 'GET' : 'POST',headers,...(body === undefined ? {} : {body:JSON.stringify(body)})});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Request failed');
  return result;
}
function node(tag, text, className) { const n = document.createElement(tag); n.textContent=text; if(className)n.className=className; return n; }
function render(value) {
  current=value; el('results').hidden=false; el('save').disabled=false;
  el('summary').replaceChildren();
  for(const verdict of ['supported','contradicted','unknown']) {
    const box=node('div',''); box.append(node('strong',String(value.report.criteria.filter(c=>c.verdict===verdict).length)),node('span',verdict)); el('summary').append(box);
  }
  el('criteria').replaceChildren(); el('criterion').replaceChildren();
  for(const c of value.report.criteria) {
    const card=node('article','','criterion'); card.append(node('span',c.kind.toUpperCase(),'eyebrow'),node('h2',c.statement),node('span',c.verdict,'tag '+c.verdict),node('p',c.review_signal.replaceAll('_',' ')));
    for(const cite of c.citations) {card.append(node('blockquote',cite.quote),node('code',`${cite.source_id} · ${cite.source_version} · characters ${cite.start}–${cite.end}`));}
    for(const missing of c.missing_information)card.append(node('p',missing));
    const latest = value.audit.filter(a=>a.event.action==='correction' && a.event.criterion_id===c.criterion_id).at(-1);
    if(latest) card.append(node('p',`Latest reviewer assertion: ${latest.event.verdict} — ${latest.event.reviewer}. Reason: ${latest.event.reason}`,'review-assertion'));
    el('criteria').append(card); const option=node('option',c.criterion_id); option.value=c.criterion_id; el('criterion').append(option);
  }
  el('audit').replaceChildren();
  for(const a of value.audit)el('audit').append(node('div',`${a.event.at} · ${a.event.action} · revision ${a.event.revision}${a.event.reason ? ' · '+a.event.reviewer+': '+a.event.verdict+' — '+a.event.reason : ''}`,'audit-entry'));
  el('status').textContent=`Report ${value.id} · revision ${value.revision} · ${value.report.execution.tool_calls} tool calls. Saved locally.`;
}
el('run').addEventListener('click',async()=>{el('run').disabled=true;el('status').textContent='Investigating…';try{render(await api('/v1/investigate',JSON.parse(el('request').value)));}catch(e){el('status').textContent='Investigation failed: '+e.message;}finally{el('run').disabled=false;}});
el('refresh-history').addEventListener('click',async()=>{try{const saved=await api('/v1/reports');el('history').replaceChildren();for(const report of saved.reports){const button=node('button',`${report.id} · revision ${report.revision}`,'secondary');button.addEventListener('click',async()=>{try{render(await api('/v1/reports/'+report.id));}catch(error){el('status').textContent=error.message;}});el('history').append(button);}}catch(error){el('status').textContent=error.message;}});
el('html-export').addEventListener('click',async()=>{if(!current)return;try{const response=await fetch('/v1/export/'+current.id,{headers:accessToken?{Authorization:'Bearer '+accessToken}:{}});if(!response.ok)throw new Error('Export failed');const url=URL.createObjectURL(await response.blob());const link=document.createElement('a');link.href=url;link.download='triallens-evidence.html';link.click();URL.revokeObjectURL(url);}catch(error){el('status').textContent=error.message;}});
el('correction').addEventListener('submit',async e=>{e.preventDefault();if(!current)return;el('save').disabled=true;try{render(await api('/v1/reviews',{identifier:current.id,revision:current.revision,criterion_id:el('criterion').value,verdict:el('verdict').value,reason:el('reason').value,reviewer:el('reviewer').value}));el('reason').value='';}catch(error){el('status').textContent='Correction failed: '+error.message;}finally{el('save').disabled=false;}});
el('export').addEventListener('click',()=>{if(!current)return;const url=URL.createObjectURL(new Blob([JSON.stringify(current,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='triallens-review.json';a.click();URL.revokeObjectURL(url);});
async function loadDemo() {const request=await api('/v1/demo');el('request').value=JSON.stringify(request,null,2);el('status').textContent='Synthetic demo ready.';}
el('login').addEventListener('submit',async event=>{event.preventDefault();accessToken=el('token').value;el('token').value='';try{const me=await api('/v1/me');el('identity').textContent='Connected as '+me.reviewer;el('reviewer').value=me.reviewer;el('reviewer').readOnly=true;await loadDemo();}catch(error){accessToken='';el('identity').textContent='Connection failed: '+error.message;}});
el('logout').addEventListener('click',()=>{accessToken='';current=null;el('request').value='';el('reviewer').value='';el('reviewer').readOnly=false;el('results').hidden=true;el('audit').replaceChildren();el('criteria').replaceChildren();el('history').replaceChildren();el('save').disabled=true;el('identity').textContent='Disconnected. Access token cleared.';});
loadDemo().catch(()=>{el('status').textContent='Connect with your reviewer token to load the case.';});
