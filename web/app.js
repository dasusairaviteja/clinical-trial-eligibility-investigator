'use strict';
const patients = [
  {id:'SYN-001',name:'Alex Morgan',age:54,sex:'Female',condition:'Type 2 diabetes',initials:'AM'},
  {id:'SYN-002',name:'Jordan Lee',age:42,sex:'Male',condition:'Type 2 diabetes',initials:'JL'},
  {id:'SYN-003',name:'Casey Rivera',age:67,sex:'Female',condition:'Reduced mobility',initials:'CR'}
];
const trials = {
  'DEMO-101':{title:'Metabolic health & daily activity',description:'A fictional observational study exploring metabolic health and everyday activity.',tags:['Observational','Adult cohort']},
  'DEMO-202':{title:'Movement & healthy aging',description:'A fictional study of daily mobility in older adults. For interface evaluation only.',tags:['Observational','Mobility']}
};
const $ = selector => document.querySelector(selector);
const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let reviews={};
try { const stored=JSON.parse(localStorage.getItem('triallens-reviews-v1')||'{}'); if(stored && typeof stored==='object' && !Array.isArray(stored)) reviews=stored; } catch {}
let activePatient=patients[0],activeTrial='DEMO-101',selected=0,filter='all',criteria=[];
let toastTimer;
function toast(message){$('#toast').textContent=message;$('#toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('visible'),3500);}
function reviewKey(c){return `${activePatient.id}:${activeTrial}:${c.id}`;}
function buildCriteria(patient,trial){
 const mobility=trial==='DEMO-202';
 return [
  {id:'INC-01',type:'Inclusion',title:mobility?'Age 60 years or older':'Age between 18 and 65 years',status:mobility?(patient.age>=60?'supported':'contradicted'):(patient.age<=65?'supported':'contradicted'),source:'Synthetic demographics',evidence:`Age recorded as ${patient.age} years at the example assessment date.`,date:'2026-09-20',meaning:'Age is compared with the authored example threshold.'},
  {id:'INC-02',type:'Inclusion',title:mobility?'Documented mobility limitation':'Documented type 2 diabetes',status:patient.condition===(mobility?'Reduced mobility':'Type 2 diabetes')?'supported':'unknown',source:'Synthetic condition summary',evidence:`The example condition summary lists: ${patient.condition}.`,date:'2026-09-18',meaning:'A condition not listed in this summary remains unknown; absence is not proof of a negative.'},
  {id:'INC-03',type:'Inclusion',title:'Willingness to attend follow-up visits',status:'unknown',source:'No evidence available',evidence:'Willingness to attend follow-up is not documented in this example record.',date:null,meaning:'Ask the participant or reviewer to establish this information. Do not infer consent.'},
  {id:'EXC-01',type:'Exclusion',title:'Participation in another active study',status:'contradicted',source:'Synthetic research intake',evidence:'Example intake explicitly states no current participation in another research study.',date:'2026-09-20',meaning:'This exclusion statement is contradicted by the example evidence. That alone does not establish eligibility.'},
  {id:'EXC-02',type:'Exclusion',title:'Hospital admission within the past 30 days',status:'unknown',source:'Incomplete encounter history',evidence:'The example record does not contain a complete encounter history for the relevant 30-day window.',date:null,meaning:'A missing hospitalization entry is not evidence of no hospitalization. Clarification is needed.'},
  {id:'INC-04',type:'Inclusion',title:'Available baseline activity assessment',status:'supported',source:'Synthetic activity record',evidence:'A baseline activity assessment is marked complete in the example record.',date:'2026-09-19',meaning:'This authored fixture demonstrates how a positive evidence reference appears.'}
 ];
}
function patientCard(p){return `<div class="patient-card"><div class="initials">${p.initials}</div><strong>${p.name}</strong><p>${p.id} · Fictional record</p><div class="meta-row"><span>Age / sex</span><b>${p.age} years / ${p.sex}</b></div><div class="meta-row"><span>Assessment</span><b>20 Sep 2026</b></div><span class="tag">${p.condition}</span><span class="tag">Synthetic</span></div>`;}
function context(){const p=patients.find(p=>p.id===$('#patient').value);$('#patient-summary').innerHTML=patientCard(p);const t=trials[$('#trial').value];$('#trial-summary').innerHTML=`<div class="trial-description">${t.tags.map(t=>`<span class="tag">${t}</span>`).join('')}<strong>${t.title}</strong>${t.description}</div>`;}
function render(){
 $('#total-count').textContent=criteria.length;
 $('#supported-count').textContent=criteria.filter(c=>c.status==='supported').length;
 $('#unknown-count').textContent=criteria.filter(c=>c.status==='unknown').length;
 const done=criteria.filter(c=>reviews[reviewKey(c)]?.reviewed).length;
 $('#reviewed-count').innerHTML=`${done}<span> / ${criteria.length}</span>`;
 $('#case-label').textContent=activeTrial;
 const query=$('#search').value.toLowerCase().trim();
 const visible=criteria.map((c,i)=>({...c,index:i})).filter(c=>(filter==='all'||c.status===filter)&&`${c.title} ${c.evidence}`.toLowerCase().includes(query));
 if(!visible.some(c=>c.index===selected)) selected=visible[0]?.index??-1;
 $('#criteria-list').innerHTML=visible.length?visible.map(c=>`<button class="criterion ${selected===c.index?'selected':''}" data-index="${c.index}" aria-pressed="${selected===c.index}"><span class="status-icon ${c.status}">${{supported:'✓',unknown:'?',contradicted:'−'}[c.status]}</span><span class="criterion-body"><span class="criterion-top"><span>${c.id} · ${c.type.toUpperCase()}</span><span class="status-text ${c.status}">${c.status==='unknown'?'Needs clarification':c.status[0].toUpperCase()+c.status.slice(1)}</span></span><strong>${c.title}</strong><small>${c.source}${reviews[reviewKey(c)]?.reviewed?' · Reviewed':''}</small></span><span class="arrow">›</span></button>`).join(''):'<div class="empty">No matching criteria. Try another search or filter.</div>';
 renderDetail();
}
function renderDetail(){const c=criteria[selected];if(!c){$('#detail').innerHTML='<div class="section-kicker">03 / SOURCE DETAIL</div><h2>No criterion selected</h2><p class="detail-description">Clear your search to explore the case evidence.</p>';return;}
 const r=reviews[reviewKey(c)]||{};
 $('#detail').innerHTML=`<div class="section-kicker">03 / SOURCE DETAIL</div><h2>The evidence behind it.</h2><p class="detail-description">${activePatient.name} · ${activeTrial}</p><span class="pill ${c.status}">${c.status==='unknown'?'Needs clarification':c.status}</span><h3>${c.title}</h3><div class="evidence"><div class="source-label">${c.source.toUpperCase()}</div><blockquote>“${c.evidence}”</blockquote><small>${c.date||'Date unavailable'} · Authored demo fixture</small></div><div class="meaning"><strong>How to interpret this</strong>${c.meaning}</div><div class="divider"></div><label for="review-note">Your review note · synthetic data only</label><textarea id="review-note" maxlength="1000" placeholder="Add a clarification or next step…">${escapeHtml(typeof r.note==='string'?r.note:'')}</textarea><button id="save-review" class="button primary full">${r.reviewed?'Update review':'Mark reviewed'} <span>✓</span></button><p class="review-status">${r.reviewed?'Reviewed · saved in this browser':'Pending human review'}</p>`;
 $('#save-review').addEventListener('click',()=>{const key=reviewKey(c);const previous=reviews[key];reviews[key]={note:$('#review-note').value,reviewed:true,time:new Date().toISOString(),patient:activePatient.id,trial:activeTrial,criterion:c.id};try{localStorage.setItem('triallens-reviews-v1',JSON.stringify(reviews));render();toast('Review saved on this browser.');}catch{if(previous)reviews[key]=previous;else delete reviews[key];toast('Unable to save. Browser storage is unavailable.');}});
}
function switchView(view){document.querySelectorAll('.nav').forEach(b=>b.classList.toggle('active',b.dataset.view===view));for(const v of ['screening','patients','activity','guide','dataset'])$(`#${v}-view`).hidden=v!==view;$('#breadcrumb').textContent={screening:'Screening',patients:'Synthetic patients',activity:'Review activity',dataset:'Trial library',guide:'Research guide'}[view];$('#page-title').textContent={screening:'Clarity at every criterion.',patients:'People behind the evidence.',activity:'A trace of every review.',dataset:'Explore the trial evidence.',guide:'Understand before you infer.'}[view];$('#export').hidden=view!=='screening';
 if(view==='dataset') loadDataset();
 if(view==='patients')$('#patients-view').innerHTML='<h2>Your synthetic cohort</h2><p>Three fictional records for exploring the interface. No real patient data is accepted.</p><div class="patient-grid">'+patients.map(patientCard).join('')+'</div>';
 if(view==='activity'){const items=Object.values(reviews).filter(r=>r&&typeof r==='object'&&r.reviewed).sort((a,b)=>String(b.time).localeCompare(String(a.time)));$('#activity-view').innerHTML='<h2>Local review history</h2><p>Latest saved state per criterion, on this browser only. This is not an immutable audit log.</p>'+ (items.length?items.map(r=>`<div class="activity-item"><strong>${escapeHtml(r.patient)} / ${escapeHtml(r.trial)} / ${escapeHtml(r.criterion)}</strong><p>${escapeHtml(r.note||'Reviewed without a note.')}</p><small>${escapeHtml(r.time)}</small></div>`).join(''):'<div class="empty">No reviews yet. Mark a criterion reviewed to see it here.</div>');}
 if(view==='guide')$('#guide-view').innerHTML='<h2>Evidence first. Judgment second.</h2><p>This preview demonstrates the review experience using authored fixtures. It does not retrieve live trials, call an AI model, diagnose, or determine eligibility.</p><h3>Read the criterion polarity</h3><p>Supported means the statement is supported by the example record. For an exclusion criterion, that can be a reason to exclude. Contradicted and unknown are distinct: missing evidence must remain unknown.</p><h3>What works today</h3><ul><li>Switch fictional patient and trial pairs, then load a demonstration.</li><li>Search and filter criteria, inspect source evidence, and save a review note.</li><li>Export a JSON record of the current case and saved reviews.</li></ul><h3>Still to come</h3><p>Validated data contracts, public trial retrieval, the bounded investigation agent, expert-reviewed labels, secure persistence, and Azure deployment.</p>';
}
$('#patient').innerHTML=patients.map(p=>`<option value="${p.id}">${p.name} · ${p.id}</option>`).join('');
$('#patient').addEventListener('change',context);$('#trial').addEventListener('change',context);
$('#load').addEventListener('click',()=>{activePatient=patients.find(p=>p.id===$('#patient').value);activeTrial=$('#trial').value;criteria=buildCriteria(activePatient,activeTrial);selected=0;filter='all';$('#search').value='';document.querySelectorAll('.filter').forEach(b=>b.classList.toggle('active',b.dataset.filter==='all'));render();toast(`Loaded ${activePatient.id} / ${activeTrial} demonstration.`);});
$('#search').addEventListener('input',render);
$('.filters').addEventListener('click',e=>{const b=e.target.closest('[data-filter]');if(!b)return;filter=b.dataset.filter;document.querySelectorAll('.filter').forEach(b=>b.classList.toggle('active',b.dataset.filter===filter));render();});
$('#criteria-list').addEventListener('click',e=>{const b=e.target.closest('[data-index]');if(!b)return;selected=Number(b.dataset.index);render();});
document.querySelectorAll('.nav').forEach(b=>b.addEventListener('click',()=>switchView(b.dataset.view)));
$('#export').addEventListener('click',()=>{const report={schemaVersion:1,mode:'authored-synthetic-demo',clinicalDecision:false,patientId:activePatient.id,trialId:activeTrial,exportedAt:new Date().toISOString(),criteria:criteria.map(c=>({...c,review:reviews[reviewKey(c)]||null}))};const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`triallens-${activePatient.id}-${activeTrial}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Synthetic review exported.');});
context();criteria=buildCriteria(activePatient,activeTrial);render();

async function loadDataset(){
 const container=$('#dataset-view');
 container.innerHTML='<h2>Local trial library</h2><p>Loading the imported historical snapshot…</p>';
 try{
  const response=await fetch('local-trials.json');
  if(!response.ok) throw new Error('Not imported');
  const data=await response.json();
  container.innerHTML=`<h2>Historical trial snapshot</h2><p>${Number(data.imported)} local records from ${Number(data.totalXmlEntries).toLocaleString()} XML entries. Recruitment status is historical, not verified live. These records are separate from the fictional screening demonstration.</p><label for="trial-search">Search imported titles, identifiers or conditions</label><input id="trial-search" type="search" style="width:100%;padding:12px" placeholder="Search trial library…"><div id="trial-results"></div>`;
  const show=()=>{const q=$('#trial-search').value.toLowerCase();const matches=data.trials.filter(t=>`${t.title} ${t.id} ${t.conditions.join(' ')}`.toLowerCase().includes(q));$('#trial-results').innerHTML=matches.length?matches.slice(0,30).map(t=>`<details class="activity-item"><summary><strong>${escapeHtml(t.id)} · ${escapeHtml(t.title)}</strong></summary><p>${escapeHtml(t.status)} · Last updated: ${escapeHtml(t.updated||'unknown')}</p><p style="white-space:pre-wrap">${escapeHtml(t.eligibility||'Eligibility text unavailable')}</p></details>`).join(''):'<p>No matching trials.</p>';};
  $('#trial-search').addEventListener('input',show);show();
 }catch{container.innerHTML='<h2>Connect your local trial archive</h2><p>The dataset is kept out of the public repository. Run the import command in the README, then reload this view. The screening workspace remains available with fictional examples.</p>';}
}
