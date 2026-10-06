'use strict';
const el = id => document.getElementById(id);
let current = null;
async function api(path, body) {
  const response = await fetch(path, body === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
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
    el('criteria').append(card); const option=node('option',c.criterion_id); option.value=c.criterion_id; el('criterion').append(option);
  }
  el('audit').replaceChildren();
  for(const a of value.audit)el('audit').append(node('div',`${a.event.at} · ${a.event.action} · revision ${a.event.revision}${a.event.reason ? ' · '+a.event.reviewer+': '+a.event.verdict+' — '+a.event.reason : ''}`,'audit-entry'));
  el('status').textContent=`Report ${value.id} · revision ${value.revision} · ${value.report.execution.tool_calls} tool calls. Saved locally.`;
}
el('run').addEventListener('click',async()=>{el('run').disabled=true;el('status').textContent='Investigating…';try{render(await api('/v1/investigate',JSON.parse(el('request').value)));}catch(e){el('status').textContent='Investigation failed: '+e.message;}finally{el('run').disabled=false;}});
el('correction').addEventListener('submit',async e=>{e.preventDefault();if(!current)return;el('save').disabled=true;try{render(await api('/v1/reviews',{identifier:current.id,revision:current.revision,criterion_id:el('criterion').value,verdict:el('verdict').value,reason:el('reason').value,reviewer:el('reviewer').value}));el('reason').value='';}catch(error){el('status').textContent='Correction failed: '+error.message;}finally{el('save').disabled=false;}});
el('export').addEventListener('click',()=>{if(!current)return;const url=URL.createObjectURL(new Blob([JSON.stringify(current,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='triallens-review.json';a.click();URL.revokeObjectURL(url);});
api('/v1/demo').then(request=>{el('request').value=JSON.stringify(request,null,2);el('status').textContent='Synthetic demo ready.';}).catch(()=>{el('status').textContent='Could not load demo. Check the API.';});
