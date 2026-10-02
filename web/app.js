'use strict';
/* =====================================================================
   TrialLens — Clinical Trial Eligibility Investigator (research preview)
   Static single-page app. All records are authored synthetic fixtures.
   No model calls, no network clinical data, no real patients.
   ===================================================================== */

/* ---------------- utils ---------------- */
const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
const esc = v => String(v == null ? '' : v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const fmtDate = iso => { if (!iso) return 'Date unavailable'; const d = new Date(iso + 'T12:00:00'); return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`; };
const daysBetween = (a, b) => Math.round((new Date(b) - new Date(a)) / 86400000);
const store = {
  get(k, fb) { try { const v = JSON.parse(localStorage.getItem(k)); return v == null ? fb : v; } catch { return fb; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); return true; } catch { return false; } }
};
let toastTimer;
function toast(msg) { const t = $('#toast'); t.textContent = msg; t.classList.add('visible'); clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove('visible'), 3600); }

/* ---------------- synthetic data ----------------
   Authored fixtures. Deterministic rule evaluation below. */
const ASSESSMENT = '2026-09-20';
const PATIENTS = [
  { id:'SYN-001', name:'Alex Morgan', age:54, sex:'Female', initials:'AM',
    conditions:[{label:'Type 2 diabetes', since:'2019-03-14'},{label:'Hyperlipidemia', since:'2021-06-02'}],
    medications:[{name:'Metformin', dose:'1000 mg twice daily', start:'2019-04-02', end:null},{name:'Atorvastatin', dose:'20 mg daily', start:'2021-06-10', end:null}],
    encounters:[{date:'2026-09-20', type:'Outpatient visit', note:'Routine diabetes review. Reports steady energy.'},{date:'2026-06-11', type:'Lab draw', note:'HbA1c and lipid panel.'},{date:'2026-02-03', type:'Outpatient visit', note:'Medication review, no changes.'}],
    labs:[{name:'HbA1c', value:7.2, unit:'%', date:'2026-06-11'},{name:'eGFR', value:88, unit:'mL/min', date:'2026-06-11'}] },
  { id:'SYN-002', name:'Jordan Lee', age:42, sex:'Male', initials:'JL',
    conditions:[{label:'Type 2 diabetes', since:'2022-01-19'},{label:'Hypertension', since:'2022-01-19'}],
    medications:[{name:'Metformin', dose:'500 mg twice daily', start:'2022-02-01', end:null},{name:'Lisinopril', dose:'10 mg daily', start:'2022-02-01', end:null}],
    encounters:[{date:'2026-09-20', type:'Outpatient visit', note:'Blood pressure recheck, lifestyle counseling.'},{date:'2026-07-28', type:'Lab draw', note:'Metabolic panel.'}],
    labs:[{name:'HbA1c', value:6.8, unit:'%', date:'2026-07-28'},{name:'Systolic BP', value:138, unit:'mmHg', date:'2026-09-20'}] },
  { id:'SYN-003', name:'Casey Rivera', age:67, sex:'Female', initials:'CR',
    conditions:[{label:'Reduced mobility', since:'2024-11-05'},{label:'Osteoarthritis, knee', since:'2023-08-17'}],
    medications:[{name:'Acetaminophen', dose:'as needed', start:'2023-08-20', end:null}],
    encounters:[{date:'2026-09-20', type:'Outpatient visit', note:'Mobility assessment, gait aid review.'},{date:'2026-08-02', type:'Emergency visit', note:'Fall at home, no fracture. Discharged same day.'},{date:'2026-04-15', type:'Physiotherapy', note:'Gait training session 6 of 8.'}],
    labs:[{name:'Vitamin D', value:28, unit:'ng/mL', date:'2026-04-15'}] },
  { id:'SYN-004', name:'Sam Ortiz', age:71, sex:'Male', initials:'SO',
    conditions:[{label:'Hypertension', since:'2018-05-30'},{label:'COPD', since:'2020-09-12'}],
    medications:[{name:'Amlodipine', dose:'5 mg daily', start:'2018-06-04', end:null},{name:'Tiotropium', dose:'daily inhaler', start:'2020-09-20', end:null}],
    encounters:[{date:'2026-09-20', type:'Outpatient visit', note:'COPD action plan review.'},{date:'2026-08-06', type:'Inpatient admission', note:'COPD exacerbation, 3-day stay. Discharged 2026-08-09.'},{date:'2026-05-19', type:'Outpatient visit', note:'Blood pressure check.'}],
    labs:[{name:'Systolic BP', value:146, unit:'mmHg', date:'2026-09-20'},{name:'FEV1', value:62, unit:'% predicted', date:'2026-05-19'}] },
  { id:'SYN-005', name:'Riley Chen', age:38, sex:'Female', initials:'RC',
    conditions:[{label:'Asthma', since:'2015-02-11'}],
    medications:[{name:'Albuterol', dose:'inhaler as needed', start:'2015-02-15', end:null},{name:'Fluticasone', dose:'daily inhaler', start:'2023-01-09', end:null}],
    encounters:[{date:'2026-09-20', type:'Outpatient visit', note:'Asthma control check, inhaler technique reviewed.'},{date:'2026-03-14', type:'Urgent care', note:'Asthma flare, treated and released.'}],
    labs:[{name:'Peak flow', value:420, unit:'L/min', date:'2026-09-20'}] },
  { id:'SYN-006', name:'Taylor Brooks', age:59, sex:'Male', initials:'TB',
    conditions:[{label:'Type 2 diabetes', since:'2024-02-22'}],
    medications:[],
    encounters:[{date:'2026-09-20', type:'Outpatient visit', note:'New patient intake, history taken.'}],
    labs:[] },
];

/* Criterion rule kinds:
   ageRange | conditionPresent | noRecentEncounter | medActive | noMedWithin |
   labBelow | labAbove | unknown (no data source: demonstrates abstention) */
const TRIALS = [
  { id:'SYN-DIAB-01', title:'Metabolic health & daily activity', kind:'Observational',
    desc:'A fictional observational study exploring metabolic health and everyday activity in adults with diabetes.',
    tags:['Observational','Adult cohort'],
    criteria:[
      { id:'INC-01', type:'Inclusion', title:'Age between 18 and 65 years', rule:{kind:'ageRange', min:18, max:65} },
      { id:'INC-02', type:'Inclusion', title:'Documented type 2 diabetes', rule:{kind:'conditionPresent', label:'Type 2 diabetes'} },
      { id:'INC-03', type:'Inclusion', title:'HbA1c below 8.0% within the last year', rule:{kind:'labBelow', name:'HbA1c', threshold:8.0, unit:'%', withinDays:365} },
      { id:'INC-04', type:'Inclusion', title:'Currently prescribed metformin', rule:{kind:'medActive', name:'Metformin'} },
      { id:'INC-05', type:'Inclusion', title:'Willingness to attend follow-up visits', rule:{kind:'unknown', missing:'Willingness to attend follow-up is not documented in this record.'} },
      { id:'EXC-01', type:'Exclusion', title:'Participation in another active study', rule:{kind:'unknown', missing:'Research participation history is not captured in this record.'} },
      { id:'EXC-02', type:'Exclusion', title:'Hospital admission within the past 30 days', rule:{kind:'noRecentEncounter', etype:'Inpatient admission', days:30} },
      { id:'EXC-03', type:'Exclusion', title:'eGFR below 45 mL/min', rule:{kind:'labBelow', name:'eGFR', threshold:45, unit:'mL/min', withinDays:365, invert:true} },
    ]},
  { id:'SYN-MOB-02', title:'Movement & healthy aging', kind:'Observational',
    desc:'A fictional study of daily mobility in older adults. For interface evaluation only.',
    tags:['Observational','Mobility'],
    criteria:[
      { id:'INC-01', type:'Inclusion', title:'Age 60 years or older', rule:{kind:'ageRange', min:60, max:120} },
      { id:'INC-02', type:'Inclusion', title:'Documented mobility limitation', rule:{kind:'conditionPresent', label:'Reduced mobility'} },
      { id:'INC-03', type:'Inclusion', title:'Ambulatory with or without a gait aid', rule:{kind:'unknown', missing:'Gait-aid use is mentioned only in free-text notes, not as structured data.'} },
      { id:'INC-04', type:'Inclusion', title:'Available baseline activity assessment', rule:{kind:'unknown', missing:'No baseline activity assessment is recorded for this patient.'} },
      { id:'EXC-01', type:'Exclusion', title:'Fall with injury in the past 90 days', rule:{kind:'noRecentEncounter', etype:'Emergency visit', days:90, noteMatch:'fall'} },
      { id:'EXC-02', type:'Exclusion', title:'Hospital admission within the past 30 days', rule:{kind:'noRecentEncounter', etype:'Inpatient admission', days:30} },
    ]},
  { id:'SYN-CARD-03', title:'Blood pressure control study', kind:'Interventional (fictional)',
    desc:'A fictional interventional study of blood pressure management in hypertension.',
    tags:['Interventional','Cardiology'],
    criteria:[
      { id:'INC-01', type:'Inclusion', title:'Age between 40 and 80 years', rule:{kind:'ageRange', min:40, max:80} },
      { id:'INC-02', type:'Inclusion', title:'Documented hypertension', rule:{kind:'conditionPresent', label:'Hypertension'} },
      { id:'INC-03', type:'Inclusion', title:'Systolic BP above 130 mmHg at screening', rule:{kind:'labAbove', name:'Systolic BP', threshold:130, unit:'mmHg', withinDays:60} },
      { id:'INC-04', type:'Inclusion', title:'On a stable antihypertensive for 30+ days', rule:{kind:'medActive', name:'__antihypertensive', minDays:30} },
      { id:'EXC-01', type:'Exclusion', title:'COPD requiring daily inhaler', rule:{kind:'medActive', name:'Tiotropium'} },
      { id:'EXC-02', type:'Exclusion', title:'Hospital admission within the past 30 days', rule:{kind:'noRecentEncounter', etype:'Inpatient admission', days:30} },
      { id:'EXC-03', type:'Exclusion', title:'Pregnancy', rule:{kind:'unknown', missing:'Pregnancy status is not recorded in this record.'} },
    ]},
  { id:'SYN-RESP-04', title:'Asthma control program', kind:'Observational',
    desc:'A fictional program evaluating asthma control strategies.',
    tags:['Observational','Respiratory'],
    criteria:[
      { id:'INC-01', type:'Inclusion', title:'Age between 18 and 65 years', rule:{kind:'ageRange', min:18, max:65} },
      { id:'INC-02', type:'Inclusion', title:'Documented asthma diagnosis', rule:{kind:'conditionPresent', label:'Asthma'} },
      { id:'INC-03', type:'Inclusion', title:'Rescue inhaler prescribed', rule:{kind:'medActive', name:'Albuterol'} },
      { id:'INC-04', type:'Inclusion', title:'No systemic corticosteroids in the past 14 days', rule:{kind:'noMedWithin', name:'Prednisone', days:14} },
      { id:'EXC-01', type:'Exclusion', title:'Urgent care visit for asthma in the past 30 days', rule:{kind:'noRecentEncounter', etype:'Urgent care', days:30, noteMatch:'asthma'} },
      { id:'EXC-02', type:'Exclusion', title:'Current smoker', rule:{kind:'unknown', missing:'Smoking status is not captured in this record.'} },
    ]},
];
const ANTIHYPERTENSIVES = ['Lisinopril','Amlodipine','Losartan','Metoprolol','Hydrochlorothiazide'];

/* ---------------- deterministic evaluation engine ---------------- */
function medActiveOn(med, date) { return med.start <= date && (!med.end || med.end >= date); }
function evaluateCriterion(patient, criterion) {
  const r = criterion.rule, asOf = ASSESSMENT;
  const temporal = ['noRecentEncounter','noMedWithin'].includes(r.kind);
  const wrap = (status, evidence, source, date, meaning) => ({ status, evidence, source, date, meaning, temporal });
  switch (r.kind) {
    case 'ageRange': {
      const ok = patient.age >= r.min && patient.age <= r.max;
      return wrap(ok ? 'supported' : 'contradicted',
        `Age recorded as ${patient.age} years at the assessment date (${fmtDate(asOf)}); criterion requires ${r.min}–${r.max} years.`,
        'Synthetic demographics', asOf,
        ok ? 'Age falls inside the authored eligibility window.' : 'Age falls outside the authored eligibility window.');
    }
    case 'conditionPresent': {
      const c = patient.conditions.find(c => c.label === r.label);
      if (c) return wrap('supported', `Condition list includes "${c.label}" (recorded ${fmtDate(c.since)}).`, 'Synthetic condition summary', c.since, 'A listed condition is treated as documented evidence.');
      return wrap('unknown', `The condition summary does not list "${r.label}".`, 'Synthetic condition summary', null, 'Absence from the summary is not proof of absence. Clarification needed.');
    }
    case 'noRecentEncounter': {
      const hits = patient.encounters.filter(e => e.type === r.etype && (!r.noteMatch || e.note.toLowerCase().includes(r.noteMatch)) && daysBetween(e.date, asOf) <= r.days && daysBetween(e.date, asOf) >= 0);
      if (hits.length) { const h = hits[0]; return wrap('supported', `${h.type} on ${fmtDate(h.date)} — ${Math.abs(daysBetween(h.date, asOf))} days before assessment, inside the ${r.days}-day window. Note: ${h.note}`, 'Synthetic encounter history', h.date, 'For an exclusion criterion, a supported statement is a potential reason to exclude — not a verdict.'); }
      const recent = patient.encounters.filter(e => daysBetween(e.date, asOf) <= r.days && daysBetween(e.date, asOf) >= 0);
      if (!recent.length && r.days <= 90) return wrap('unknown', `No encounter records exist at all within the ${r.days}-day window before ${fmtDate(asOf)}.`, 'Incomplete encounter history', null, 'A missing encounter entry is not evidence of no encounter. Clarification needed.');
      return wrap('contradicted', `No ${r.etype.toLowerCase()} recorded in the ${r.days} days before ${fmtDate(asOf)}; ${recent.length} other encounter(s) in window.`, 'Synthetic encounter history', asOf, 'The exclusion statement is contradicted by the available history.');
    }
    case 'medActive': {
      const names = r.name === '__antihypertensive' ? ANTIHYPERTENSIVES : [r.name];
      const m = patient.medications.find(m => names.includes(m.name) && medActiveOn(m, asOf));
      if (m) { const days = daysBetween(m.start, asOf); const stable = !r.minDays || days >= r.minDays;
        return wrap(stable ? 'supported' : 'unknown', `${m.name} ${m.dose || ''} started ${fmtDate(m.start)} (${days} days before assessment)${m.end ? `, ended ${fmtDate(m.end)}` : ', no end date — treated as active'}.`, 'Synthetic medication list', m.start, stable ? 'Active prescription found in the authored record.' : `Started only ${days} days ago; the ${r.minDays}-day stability window cannot be confirmed.`); }
      return wrap('unknown', `No active prescription for ${r.name === '__antihypertensive' ? 'an antihypertensive' : r.name} in the medication list.`, 'Synthetic medication list', null, 'The medication list may be incomplete. Do not infer non-use.');
    }
    case 'noMedWithin': {
      const hits = patient.medications.filter(m => m.name === r.name && m.start <= asOf && daysBetween(m.start, asOf) <= r.days);
      if (hits.length) return wrap('supported', `${r.name} started ${fmtDate(hits[0].start)}, inside the ${r.days}-day window.`, 'Synthetic medication list', hits[0].start, 'For an exclusion criterion, this is a potential reason to exclude.');
      return wrap('contradicted', `No ${r.name} prescription started within ${r.days} days of ${fmtDate(asOf)}.`, 'Synthetic medication list', asOf, 'The exclusion statement is contradicted by the medication history.');
    }
    case 'labBelow': case 'labAbove': {
      const labs = patient.labs.filter(l => l.name === r.name && daysBetween(l.date, asOf) <= r.withinDays && daysBetween(l.date, asOf) >= 0);
      if (!labs.length) return wrap('unknown', `No ${r.name} result within ${r.withinDays} days of ${fmtDate(asOf)}.`, 'Synthetic lab results', null, 'A missing lab value must remain unknown — never impute a number.');
      const lab = labs.sort((a,b) => b.date.localeCompare(a.date))[0];
      const meets = r.kind === 'labBelow' ? lab.value < r.threshold : lab.value > r.threshold;
      const finalStatus = r.invert ? (meets ? 'supported' : 'contradicted') : (meets ? 'supported' : 'contradicted');
      return wrap(finalStatus, `${r.name}: ${lab.value} ${lab.unit} on ${fmtDate(lab.date)} (threshold ${r.invert ? '' : r.kind === 'labBelow' ? '<' : '>'} ${r.threshold} ${r.unit}).`, 'Synthetic lab results', lab.date, 'Value compared against the authored threshold.');
    }
    case 'unknown':
    default:
      return wrap('unknown', r.missing || 'No data source covers this criterion in the synthetic record.', 'No evidence available', null, 'Ask the participant or reviewer. Do not infer.');
  }
}
function evaluateCase(patientId, trialId) {
  const patient = PATIENTS.find(p => p.id === patientId), trial = TRIALS.find(t => t.id === trialId);
  if (!patient || !trial) return null;
  return { patient, trial, criteria: trial.criteria.map(c => ({ ...c, result: evaluateCriterion(patient, c) })) };
}

/* ---------------- state ---------------- */
const state = {
  view: 'dashboard',
  patientId: 'SYN-001', trialId: 'SYN-DIAB-01',
  selected: 0, filter: 'all', query: '',
  compareTrial: 'SYN-DIAB-01',
  checklistTrial: 'SYN-DIAB-01',
  reportPatient: 'SYN-001', reportTrial: 'SYN-DIAB-01',
  patientDetail: null,
  libQuery: '', libPage: 0, libSort: 'title',
  libData: null, libTried: false,
};
let reviews = store.get('triallens-reviews-v1', {});
let checklist = store.get('triallens-checklist-v1', {}); // key -> {done, note, time}
const reviewKey = (p, t, c) => `${p}:${t}:${c}`;
const checkKey = (p, t, c) => `check:${p}:${t}:${c}`;
const STATUS_LABEL = { supported: 'Supported', contradicted: 'Contradicted', unknown: 'Needs clarification' };
const STATUS_ICON = { supported: '✓', contradicted: '−', unknown: '?' };

/* ---------------- svg charts ---------------- */
function donut(segments, size = 150) {
  const total = segments.reduce((a, s) => a + s.value, 0) || 1;
  const R = 60, C = 2 * Math.PI * R; let off = 0;
  const arcs = segments.map(s => {
    const len = (s.value / total) * C;
    const el = `<circle cx="75" cy="75" r="${R}" fill="none" stroke="${s.color}" stroke-width="22" stroke-dasharray="${len} ${C - len}" stroke-dashoffset="${-off}" transform="rotate(-90 75 75)"/>`;
    off += len; return el;
  }).join('');
  return `<svg class="donut" viewBox="0 0 150 150" role="img" aria-label="Verdict distribution chart">${arcs}
    <text x="75" y="70" text-anchor="middle" font-size="26" font-weight="700" fill="var(--ink)">${total}</text>
    <text x="75" y="90" text-anchor="middle" font-size="10" fill="var(--muted)">criteria</text></svg>`;
}
function bars(rows) {
  const max = Math.max(1, ...rows.map(r => r.value));
  return rows.map(r => `<div class="bar-row"><span>${esc(r.label)}</span>
    <div class="bar-track"><div class="bar-fill" style="width:${Math.round(r.value / max * 100)}%;background:${r.color}"></div></div>
    <b>${r.value}</b></div>`).join('');
}
function spark(values) {
  const max = Math.max(1, ...values);
  return `<span class="spark" aria-hidden="true">${values.map(v => `<i style="height:${Math.max(12, Math.round(v / max * 100))}%"></i>`).join('')}</span>`;
}

/* ---------------- shared fragments ---------------- */
function verdictChip(status) { return `<span class="chip ${status}">${STATUS_LABEL[status]}</span>`; }
function patientHero(p) {
  return `<div class="patient-hero"><div class="ph-top"><div class="initials">${p.initials}</div>
    <div><strong>${esc(p.name)}</strong><span class="pid">${p.id} · Fictional record</span></div></div>
    <div class="kv"><span>Age / sex</span><b>${p.age} years / ${p.sex}</b></div>
    <div class="kv"><span>Assessment</span><b>${fmtDate(ASSESSMENT)}</b></div>
    <div class="kv"><span>Conditions</span><b>${p.conditions.length}</b></div>
    <div class="kv"><span>Medications</span><b>${p.medications.length}</b></div></div>`;
}
const VIEW_TITLES = {
  dashboard: ['Morning briefing.', 'Your review queue, at a glance.'],
  screening: ['Clarity at every criterion.', 'Connect patient evidence to trial criteria. Keep the human in the decision.'],
  compare: ['One trial, every patient.', 'Spot patterns across the synthetic cohort.'],
  checklist: ['Close the evidence gaps.', 'Every unknown, tracked to a next step.'],
  report: ['The evidence-linked report.', 'A reviewer-ready record of this case.'],
  dataset: ['Explore the trial evidence.', 'Historical snapshot imported from the public registry.'],
  patients: ['People behind the evidence.', 'Fictional records for exploring the interface.'],
  activity: ['A trace of every review.', 'Saved on this browser only — not an audit log.'],
  guide: ['Understand before you infer.', 'How to read this workspace.'],
};

/* ---------------- DASHBOARD ---------------- */
function renderDashboard() {
  const cases = [];
  for (const p of PATIENTS) for (const t of TRIALS) cases.push(evaluateCase(p.id, t.id));
  const all = cases.flatMap(c => c.criteria.map(x => ({ ...x, patient: c.patient, trial: c.trial })));
  const count = s => all.filter(c => c.result.status === s).length;
  const reviewed = Object.values(reviews).filter(r => r && r.reviewed).length;
  const unknowns = all.filter(c => c.result.status === 'unknown');
  const openChecks = unknowns.filter(c => !checklist[checkKey(c.patient.id, c.trial.id, c.id)]?.done).length;
  const perTrial = TRIALS.map(t => ({ label: t.id.replace('SYN-', ''), value: unknowns.filter(c => c.trial.id === t.id).length, color: '#d9a45b' }));
  const recent = Object.values(reviews).filter(r => r && r.reviewed).sort((a, b) => String(b.time).localeCompare(String(a.time))).slice(0, 4);
  const css = getComputedStyle(document.documentElement);
  $('#dashboard-view').innerHTML = `
    <div class="dash-grid">
      <div class="dash-card span4"><h3>Corpus</h3><p class="card-sub">Synthetic cases under review</p>
        <div class="stat-row">
          <div class="stat"><span class="k">PATIENTS</span><span class="v">${PATIENTS.length}</span></div>
          <div class="stat"><span class="k">TRIALS</span><span class="v">${TRIALS.length}</span></div>
          <div class="stat"><span class="k">CASES</span><span class="v">${cases.length}</span></div>
        </div></div>
      <div class="dash-card span4"><h3>Verdict distribution</h3><p class="card-sub">All ${all.length} criterion evaluations</p>
        <div class="donut-wrap">${donut([
          { value: count('supported'), color: '#43865c' },
          { value: count('unknown'), color: '#d9a45b' },
          { value: count('contradicted'), color: '#c07a5e' }])}
          <div class="legend">
            <div class="legend-item"><span class="legend-dot" style="background:#43865c"></span>Supported<b>${count('supported')}</b></div>
            <div class="legend-item"><span class="legend-dot" style="background:#d9a45b"></span>Needs clarification<b>${count('unknown')}</b></div>
            <div class="legend-item"><span class="legend-dot" style="background:#c07a5e"></span>Contradicted<b>${count('contradicted')}</b></div>
          </div></div></div>
      <div class="dash-card span4"><h3>Review progress</h3><p class="card-sub">Human review across all cases</p>
        <div class="stat-row"><div class="stat"><span class="k">REVIEWED</span><span class="v">${reviewed}<small> / ${all.length}</small></span>
          <div class="progress-track"><div class="progress-fill" style="width:${Math.round(reviewed / all.length * 100)}%"></div></div></div>
          <div class="stat"><span class="k">OPEN GAPS</span><span class="v">${openChecks}</span></div></div>
        <p class="small muted" style="margin:12px 0 0">Unknowns need a human next step — see the checklist.</p></div>
      <div class="dash-card span6"><h3>Unknowns by trial</h3><p class="card-sub">Where evidence is thinnest ${spark(perTrial.map(r => r.value))}</p>${bars(perTrial)}</div>
      <div class="dash-card span6"><h3>Review queue</h3><p class="card-sub">Unknowns awaiting a next step</p>
        ${unknowns.filter(c => !checklist[checkKey(c.patient.id, c.trial.id, c.id)]?.done).slice(0, 4).map(c => `
          <div class="queue-item"><div class="q-body"><strong>${esc(c.patient.name)} · ${c.trial.id} · ${c.id}</strong>
          <p>${esc(c.title)}</p></div>
          <button class="button secondary btn-sm" data-goto-check="${esc(c.trial.id)}">Open</button></div>`).join('') || '<p class="muted small">Queue clear — every unknown has a next step.</p>'}
      </div>
      <div class="dash-card span12"><h3>Recent activity</h3><p class="card-sub">Latest saved reviews on this browser</p>
        <div class="activity-mini">${recent.map(r => `<div class="activity-item"><strong>${esc(r.patient)} / ${esc(r.trial)} / ${esc(r.criterion)}</strong><p>${esc(r.note || 'Reviewed without a note.')}</p><small>${esc(r.time)}</small></div>`).join('') || '<p class="muted small">No reviews yet. Open the screening workspace to begin.</p>'}</div></div>
    </div>`;
  $$('#dashboard-view [data-goto-check]').forEach(b => b.addEventListener('click', () => { state.checklistTrial = b.dataset.gotoCheck; switchView('checklist'); }));
}

/* ---------------- SCREENING ---------------- */
function currentCase() { return evaluateCase(state.patientId, state.trialId); }
function renderScreening() {
  const c = currentCase();
  $('#screening-view').innerHTML = `
    <div class="screen-grid">
      <section class="panel"><div class="panel-pad">
        <div class="section-kicker">01 / CASE CONTEXT</div><h2>Start with the patient</h2>
        <div class="field"><label for="patient">Synthetic patient</label>
          <select id="patient">${PATIENTS.map(p => `<option value="${p.id}" ${p.id === state.patientId ? 'selected' : ''}>${esc(p.name)} · ${p.id}</option>`).join('')}</select></div>
        <div id="patient-summary">${patientHero(c.patient)}</div>
        <div class="divider"></div>
        <div class="field"><label for="trial">Fictional trial</label>
          <select id="trial">${TRIALS.map(t => `<option value="${t.id}" ${t.id === state.trialId ? 'selected' : ''}>${t.id} · ${esc(t.title)}</option>`).join('')}</select></div>
        <div class="trial-tags">${c.trial.tags.map(t => `<span class="tag">${esc(t)}</span>`).join('')}</div>
        <p class="small muted">${esc(c.trial.desc)}</p>
        <button class="button primary full" id="load-case">Load case <span aria-hidden="true">↗</span></button>
        <p class="quiet small muted" style="text-align:center;margin-top:12px">Deterministic authored fixtures.<br>No model calls. No patient uploads.</p>
      </div></section>
      <section class="panel">
        <div class="criteria-toolbar">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:14px">
            <div><div class="section-kicker">02 / EVIDENCE REVIEW</div><h2 style="margin-bottom:0">Criterion by criterion</h2></div>
            <span class="chip neutral">${esc(c.trial.id)}</span>
          </div>
          <div class="search-wrap"><span aria-hidden="true">⌕</span><input id="search" type="search" placeholder="Search criteria or evidence…  ( / )" aria-label="Search criteria or evidence" value="${esc(state.query)}"></div>
          <div class="filters" role="group" aria-label="Filter criteria">
            ${['all','unknown','supported','contradicted'].map(f => `<button class="filter ${state.filter === f ? 'active' : ''}" data-filter="${f}">${f === 'all' ? 'All criteria' : STATUS_LABEL[f]}</button>`).join('')}
          </div>
        </div>
        <div class="criteria-list" id="criteria-list" role="list"></div>
        <div class="list-footer"><span class="tiny-dot" style="width:5px;height:5px;background:#88a18c;border-radius:50%"></span> Every finding stays connected to its source.</div>
      </section>
      <aside class="panel detail-sticky" id="detail" aria-label="Evidence detail"></aside>
    </div>
    <div class="screen-grid stats-grid" id="case-stats"></div>`;
  $('#patient').addEventListener('change', e => { state.patientId = e.target.value; $('#patient-summary').innerHTML = patientHero(PATIENTS.find(p => p.id === state.patientId)); });
  $('#trial').addEventListener('change', e => { state.trialId = e.target.value; });
  $('#load-case').addEventListener('click', () => { state.selected = 0; state.filter = 'all'; state.query = ''; renderScreening(); toast(`Loaded ${state.patientId} / ${state.trialId}.`); $('#main').focus({ preventScroll: true }); });
  $('#search').addEventListener('input', e => { state.query = e.target.value; renderCriteriaList(); });
  $$('#screening-view .filter').forEach(b => b.addEventListener('click', () => { state.filter = b.dataset.filter; $$('#screening-view .filter').forEach(x => x.classList.toggle('active', x === b)); renderCriteriaList(); }));
  renderCriteriaList(); renderDetail(); renderCaseStats();
}
function filteredCriteria() {
  const c = currentCase(); const q = state.query.toLowerCase().trim();
  return c.criteria.map((x, i) => ({ ...x, index: i }))
    .filter(x => (state.filter === 'all' || x.result.status === state.filter) && `${x.title} ${x.result.evidence}`.toLowerCase().includes(q));
}
function renderCaseStats() {
  const c = currentCase();
  const n = s => c.criteria.filter(x => x.result.status === s).length;
  const done = c.criteria.filter(x => reviews[reviewKey(c.patient.id, c.trial.id, x.id)]?.reviewed).length;
  $('#case-stats').innerHTML = [
    ['CRITERIA IN THIS CASE', c.criteria.length, 'Inclusion + exclusion', ''],
    ['EVIDENCE SUPPORTS', n('supported'), 'Criterion statement supported', 'var(--ok)'],
    ['NEEDS CLARIFICATION', n('unknown'), 'Missing or incomplete evidence', 'var(--amber)'],
    [`REVIEWED BY YOU`, `${done} / ${c.criteria.length}`, 'Saved on this browser only', ''],
  ].map(([k, v, sub, col]) => `<div class="panel"><div class="panel-pad" style="padding:18px 20px"><span class="section-kicker">${k}</span><div style="font-size:30px;font-weight:600;letter-spacing:-1px;margin:4px 0;${col ? `color:${col}` : ''}">${v}</div><span class="small muted">${sub}</span></div></div>`).join('');
}
function renderCriteriaList() {
  const c = currentCase(); const visible = filteredCriteria();
  if (!visible.some(x => x.index === state.selected)) state.selected = visible[0]?.index ?? -1;
  $('#criteria-list').innerHTML = visible.length ? visible.map(x => `
    <button class="criterion ${state.selected === x.index ? 'selected' : ''}" data-index="${x.index}" role="listitem" aria-pressed="${state.selected === x.index}">
      <span class="status-icon ${x.result.status}">${STATUS_ICON[x.result.status]}</span>
      <span class="criterion-body"><span class="criterion-top"><span>${x.id} · ${x.type.toUpperCase()}</span><span class="chip ${x.result.status}">${STATUS_LABEL[x.result.status]}</span></span>
      <strong>${esc(x.title)}</strong><small>${esc(x.result.source)}${reviews[reviewKey(c.patient.id, c.trial.id, x.id)]?.reviewed ? ' · ✓ Reviewed' : ''}</small></span>
      <span class="chev" aria-hidden="true">›</span></button>`).join('')
    : '<div class="empty"><span class="big">∅</span>No matching criteria. Try another search or filter.</div>';
  $$('#criteria-list .criterion').forEach(b => b.addEventListener('click', () => { state.selected = Number(b.dataset.index); renderCriteriaList(); renderDetail(); }));
  renderCaseStats();
}
function renderDetail() {
  const c = currentCase(); const x = c.criteria[state.selected]; const box = $('#detail');
  if (!x) { box.innerHTML = '<div class="panel-pad"><div class="section-kicker">03 / SOURCE DETAIL</div><h2>No criterion selected</h2><p class="small muted">Clear your search to explore the case evidence.</p></div>'; return; }
  const r = reviews[reviewKey(c.patient.id, c.trial.id, x.id)] || {};
  box.innerHTML = `<div class="panel-pad">
    <div class="section-kicker">03 / SOURCE DETAIL</div><h2>The evidence behind it.</h2>
    <p class="small muted">${esc(c.patient.name)} · ${esc(c.trial.id)}</p>
    <div style="margin:10px 0">${verdictChip(x.result.status)}${x.result.temporal ? '<span class="temporal-flag">◷ temporal check</span>' : ''}</div>
    <h3 style="line-height:1.6">${esc(x.title)}</h3>
    <div class="evidence"><div class="src">${esc(x.result.source).toUpperCase()}</div>
      <blockquote>“${esc(x.result.evidence)}”</blockquote>
      <small>${x.result.date ? fmtDate(x.result.date) : 'Date unavailable'} · Authored demo fixture</small></div>
    <div class="meaning"><strong>HOW TO INTERPRET THIS</strong>${esc(x.result.meaning)}</div>
    <div class="review-box"><div class="field"><label for="review-note">Your review note · synthetic data only</label>
      <textarea id="review-note" maxlength="1000" placeholder="Add a clarification or next step…">${esc(typeof r.note === 'string' ? r.note : '')}</textarea></div>
      <button id="save-review" class="button primary full" style="margin-top:12px">${r.reviewed ? 'Update review' : 'Mark reviewed'} <span aria-hidden="true">✓</span></button>
      <p class="review-status">${r.reviewed ? '✓ Reviewed · saved in this browser' : '○ Pending human review'}</p></div>
  </div>`;
  $('#save-review').addEventListener('click', () => {
    const key = reviewKey(c.patient.id, c.trial.id, x.id); const prev = reviews[key];
    reviews[key] = { note: $('#review-note').value, reviewed: true, time: new Date().toISOString(), patient: c.patient.id, trial: c.trial.id, criterion: x.id };
    if (store.set('triallens-reviews-v1', reviews)) { renderCriteriaList(); renderDetail(); updateChecklistBadge(); toast('Review saved on this browser.'); }
    else { if (prev) reviews[key] = prev; else delete reviews[key]; toast('Unable to save — browser storage unavailable.'); }
  });
}

/* ---------------- COMPARE ---------------- */
function renderCompare() {
  const t = TRIALS.find(t => t.id === state.compareTrial);
  const rows = t.criteria;
  $('#compare-view').innerHTML = `
    <div class="compare-controls">
      <div class="field" style="margin:0;min-width:280px"><label for="compare-trial">Trial</label>
        <select id="compare-trial">${TRIALS.map(x => `<option value="${x.id}" ${x.id === t.id ? 'selected' : ''}>${x.id} · ${esc(x.title)}</option>`).join('')}</select></div>
      <p class="small muted" style="margin:0">Click a patient name to open the case in the screening workspace.</p>
    </div>
    <div class="matrix-wrap"><table class="matrix" aria-label="Patient by criterion verdict matrix">
      <thead><tr><th scope="col">Criterion</th>${PATIENTS.map(p => `<th scope="col"><button class="btn-sm" data-open-case="${p.id}" style="border:0;background:none;font-weight:700;font-size:11px">${esc(p.name)}<br><span class="muted" style="font-weight:400">${p.id}</span></button></th>`).join('')}</tr></thead>
      <tbody>${rows.map(cr => `<tr><th scope="row"><span class="muted" style="font-size:10px">${cr.id} · ${cr.type.toUpperCase()}</span><br>${esc(cr.title)}</th>
        ${PATIENTS.map(p => { const s = evaluateCriterion(p, cr).status; return `<td class="cell ${s}" title="${esc(p.name)} — ${STATUS_LABEL[s]}">${STATUS_ICON[s]}</td>`; }).join('')}</tr>`).join('')}
      </tbody></table></div>
    <div class="matrix-legend"><span><b style="color:var(--ok)">✓</b> Supported</span><span><b style="color:var(--amber)">?</b> Needs clarification</span><span><b style="color:var(--red)">−</b> Contradicted</span>
      <span class="muted">Deterministic authored fixtures — patterns here reflect the fixture design, not model behavior.</span></div>`;
  $('#compare-trial').addEventListener('change', e => { state.compareTrial = e.target.value; renderCompare(); });
  $$('#compare-view [data-open-case]').forEach(b => b.addEventListener('click', () => { state.patientId = b.dataset.openCase; state.trialId = state.compareTrial; state.selected = 0; switchView('screening'); }));
}

/* ---------------- CHECKLIST ---------------- */
function allUnknowns(trialId) {
  const out = [];
  for (const p of PATIENTS) for (const cr of TRIALS.find(t => t.id === trialId).criteria) {
    const res = evaluateCriterion(p, cr);
    if (res.status === 'unknown') out.push({ patient: p, criterion: cr, result: res });
  }
  return out;
}
function updateChecklistBadge() {
  const open = allUnknowns(state.checklistTrial).filter(u => !checklist[checkKey(u.patient.id, state.checklistTrial, u.criterion.id)]?.done).length;
  const badge = $('#nav-checklist-count'); badge.hidden = open === 0; badge.textContent = open;
}
function renderChecklist() {
  const items = allUnknowns(state.checklistTrial);
  const open = items.filter(u => !checklist[checkKey(u.patient.id, state.checklistTrial, u.criterion.id)]?.done);
  $('#checklist-view').innerHTML = `
    <div class="section-head"><div>
      <h2 style="margin:0">${open.length} open gap${open.length === 1 ? '' : 's'} · ${items.length} total unknowns</h2>
      <p class="small muted" style="margin:4px 0 0">Trial: <select id="checklist-trial" aria-label="Trial for checklist" style="border:1px solid var(--line);border-radius:6px;padding:4px 8px;background:var(--card)">${TRIALS.map(t => `<option value="${t.id}" ${t.id === state.checklistTrial ? 'selected' : ''}>${t.id}</option>`).join('')}</select></p></div>
      <button class="button secondary" id="export-checklist">↓ Export checklist</button></div>
    <div id="check-items">${items.map((u, i) => {
      const key = checkKey(u.patient.id, state.checklistTrial, u.criterion.id);
      const saved = checklist[key] || {};
      return `<div class="check-item ${saved.done ? 'done' : ''}">
        <div class="check-num">${saved.done ? '✓' : i + 1}</div>
        <div><h3>${esc(u.patient.name)} <span class="muted">· ${u.criterion.id} — ${esc(u.criterion.title)}</span></h3>
          <p>${esc(u.result.evidence)}</p><div class="meta">Source: ${esc(u.result.source)} · ${u.criterion.type}</div>
          <input class="inline-note" data-note="${esc(key)}" placeholder="Next step — e.g. “Ask coordinator for 30-day encounter history”…" value="${esc(saved.note || '')}" aria-label="Next step note"></div>
        <div class="check-actions"><button class="btn-sm ${saved.done ? '' : 'primary'}" data-check="${esc(key)}">${saved.done ? 'Reopen' : 'Mark done'}</button></div>
      </div>`; }).join('') || '<div class="empty"><span class="big">✓</span>Queue clear.</div>'}</div>`;
  $('#checklist-trial').addEventListener('change', e => { state.checklistTrial = e.target.value; renderChecklist(); updateChecklistBadge(); });
  $$('#checklist-view [data-check]').forEach(b => b.addEventListener('click', () => {
    const key = b.dataset.check; const cur = checklist[key] || {};
    checklist[key] = { ...cur, done: !cur.done, time: new Date().toISOString() };
    if (store.set('triallens-checklist-v1', checklist)) { renderChecklist(); updateChecklistBadge(); toast(cur.done ? 'Gap reopened.' : 'Gap closed — nice.'); }
    else toast('Unable to save — browser storage unavailable.');
  }));
  $$('#checklist-view [data-note]').forEach(inp => inp.addEventListener('change', () => {
    const key = inp.dataset.note; checklist[key] = { ...(checklist[key] || {}), note: inp.value, time: new Date().toISOString() };
    store.set('triallens-checklist-v1', checklist); toast('Note saved.');
  }));
  $('#export-checklist').addEventListener('click', () => {
    const lines = [`# Missing-information checklist — ${state.checklistTrial}`, '', `Exported ${new Date().toISOString()} · synthetic demo data`, ''];
    items.forEach((u, i) => { const s = checklist[checkKey(u.patient.id, state.checklistTrial, u.criterion.id)] || {};
      lines.push(`## ${i + 1}. ${u.patient.name} · ${u.criterion.id} — ${u.criterion.title}`, `- Status: ${s.done ? 'done' : 'open'}`, `- Evidence: ${u.result.evidence}`, `- Next step: ${s.note || '—'}`, ''); });
    download(`checklist-${state.checklistTrial}.md`, lines.join('\n'), 'text/markdown'); toast('Checklist exported as Markdown.');
  });
}

/* ---------------- REPORT ---------------- */
function renderReport() {
  const p = PATIENTS.find(p => p.id === state.reportPatient), t = TRIALS.find(t => t.id === state.reportTrial);
  const ev = evaluateCase(p.id, t.id);
  const groups = ['Inclusion', 'Exclusion'].map(type => ({ type, items: ev.criteria.filter(c => c.type === type) }));
  const unknowns = ev.criteria.filter(c => c.result.status === 'unknown');
  $('#report-view').innerHTML = `
    <div class="compare-controls no-print">
      <div class="field" style="margin:0"><label for="report-patient">Patient</label>
        <select id="report-patient">${PATIENTS.map(x => `<option value="${x.id}" ${x.id === p.id ? 'selected' : ''}>${esc(x.name)} · ${x.id}</option>`).join('')}</select></div>
      <div class="field" style="margin:0"><label for="report-trial">Trial</label>
        <select id="report-trial">${TRIALS.map(x => `<option value="${x.id}" ${x.id === t.id ? 'selected' : ''}>${x.id}</option>`).join('')}</select></div>
      <button class="button secondary" id="dl-markdown">↓ Markdown</button>
    </div>
    <article class="report-doc" aria-label="Evidence-linked reviewer report">
      <div class="r-head"><div class="section-kicker">EVIDENCE-LINKED REVIEWER REPORT · SYNTHETIC DEMO</div>
        <h2>Eligibility investigation — ${esc(p.name)}</h2>
        <p class="small muted" style="margin:0">${esc(t.id)} · ${esc(t.title)}</p>
        <div class="r-meta">
          <div><span class="k">PATIENT</span>${esc(p.name)} (${p.id})<br>${p.age} years · ${p.sex}</div>
          <div><span class="k">ASSESSMENT DATE</span>${fmtDate(ASSESSMENT)}</div>
          <div><span class="k">GENERATED</span>${fmtDate(new Date().toISOString().slice(0, 10))} · authored fixtures</div>
        </div></div>
      ${groups.map(g => `<h3>${g.type} criteria</h3>${g.items.map(c => `
        <div class="report-criterion"><h4>${esc(c.title)} ${verdictChip(c.result.status)}</h4>
          <div class="ev">“${esc(c.result.evidence)}”</div>
          <div class="src-line">Source: ${esc(c.result.source)} · ${c.result.date ? fmtDate(c.result.date) : 'date unavailable'}${c.result.temporal ? ' · temporal check' : ''}</div>
          <div class="src-line" style="margin-top:6px"><b>Interpretation:</b> ${esc(c.result.meaning)}${reviews[reviewKey(p.id, t.id, c.id)]?.reviewed ? ` · <b>Reviewed:</b> ${esc(reviews[reviewKey(p.id, t.id, c.id)].note || 'no note')}` : ' · <b>Not yet reviewed</b>'}</div>
        </div>`).join('')}`).join('')}
      <div class="report-checklist"><h3>Missing-information checklist (${unknowns.length})</h3>
        <ol>${unknowns.map(c => `<li><b>${c.id} — ${esc(c.title)}:</b> ${esc(c.result.evidence)}</li>`).join('') || '<li>None — every criterion has evidence.</li>'}</ol></div>
      <p class="small muted" style="margin-top:22px"><b>Research use only.</b> This report is generated from authored synthetic fixtures. It is not a clinical determination. A supported exclusion statement is a potential reason to exclude, not evidence of eligibility. Unknown does not mean absent.</p>
      <div class="report-sign"><div>Reviewer signature<span class="sig-line"></span></div><div>Date<span class="sig-line"></span></div></div>
    </article>`;
  $('#report-patient').addEventListener('change', e => { state.reportPatient = e.target.value; renderReport(); });
  $('#report-trial').addEventListener('change', e => { state.reportTrial = e.target.value; renderReport(); });
  $('#dl-markdown').addEventListener('click', () => {
    const L = [`# Eligibility investigation — ${p.name} (${p.id})`, '', `Trial: ${t.id} — ${t.title}`, `Assessment: ${ASSESSMENT} · synthetic demo`, ''];
    for (const c of ev.criteria) L.push(`## ${c.id} [${c.type}] — ${c.title}`, `Verdict: **${STATUS_LABEL[c.result.status]}**`, `> ${c.result.evidence}`, `Source: ${c.result.source}`, '');
    L.push('## Missing-information checklist'); unknowns.forEach(c => L.push(`- ${c.id}: ${c.title}`));
    download(`report-${p.id}-${t.id}.md`, L.join('\n'), 'text/markdown'); toast('Report downloaded as Markdown.');
  });
}
function download(name, text, type) {
  const url = URL.createObjectURL(new Blob([text], { type })); const a = document.createElement('a');
  a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

/* ---------------- DATASET (trial library) ---------------- */
async function ensureLib() {
  if (state.libTried) return state.libData;
  state.libTried = true;
  try { const r = await fetch('local-trials.json'); if (!r.ok) throw 0; state.libData = await r.json(); }
  catch { state.libData = null; }
  return state.libData;
}
async function renderDataset() {
  const box = $('#dataset-view');
  box.innerHTML = '<h2>Trial library</h2><p class="muted">Loading the imported historical snapshot…</p>';
  const data = await ensureLib();
  if (!data) { box.innerHTML = `<h2>Connect your local trial archive</h2>
    <p>The dataset is kept out of the public repository (<span class="chip neutral">web/local-trials.json</span> is gitignored).</p>
    <div class="callout"><strong>To load it:</strong> run <kbd>python scripts/import_trials.py</kbd> per the README to build <kbd>web/local-trials.json</kbd> from your local registry archive, then reload this view. The screening workspace remains available with fictional examples.</div>`; return; }
  const trials = data.trials || [];
  const q = state.libQuery.toLowerCase();
  let matches = trials.filter(t => `${t.title} ${t.id} ${(t.conditions || []).join(' ')}`.toLowerCase().includes(q));
  matches.sort((a, b) => state.libSort === 'updated' ? String(b.updated).localeCompare(String(a.updated)) : String(a.title).localeCompare(String(b.title)));
  const per = 15, pages = Math.max(1, Math.ceil(matches.length / per));
  state.libPage = Math.min(state.libPage, pages - 1);
  const page = matches.slice(state.libPage * per, state.libPage * per + per);
  box.innerHTML = `<h2>Historical trial snapshot</h2>
    <p class="muted">${Number(data.imported).toLocaleString()} local records from ${Number(data.totalXmlEntries || trials.length).toLocaleString()} XML entries. Recruitment status is historical (sample record last updated 2005) — not verified live. Separate from the fictional screening demonstration.</p>
    <div class="toolbar"><input id="lib-q" type="search" placeholder="Search titles, identifiers, conditions…" value="${esc(state.libQuery)}" aria-label="Search trial library">
      <select id="lib-sort" aria-label="Sort trials"><option value="title" ${state.libSort === 'title' ? 'selected' : ''}>Sort: title</option><option value="updated" ${state.libSort === 'updated' ? 'selected' : ''}>Sort: recently updated</option></select></div>
    <div>${page.map(t => `<details class="trial-card"><summary><span class="tid">${esc(t.id)}</span><strong>${esc(t.title)}</strong><span class="chip neutral" style="margin-left:auto">${esc(t.status || 'unknown')}</span></summary>
      <div class="t-body"><div class="kv"><span>Last updated</span><b>${esc(t.updated || 'unknown')}</b></div>
      <div class="kv"><span>Conditions</span><b>${esc((t.conditions || []).slice(0, 4).join('; ') || '—')}</b></div>
      <div class="elig">${esc(t.eligibility || 'Eligibility text unavailable')}</div></div></details>`).join('') || '<div class="empty"><span class="big">∅</span>No matching trials.</div>'}</div>
    <div class="pager"><button class="btn-sm" id="lib-prev" ${state.libPage === 0 ? 'disabled' : ''}>← Prev</button>
      <span>Page ${state.libPage + 1} of ${pages} · ${matches.length.toLocaleString()} trials</span>
      <button class="btn-sm" id="lib-next" ${state.libPage >= pages - 1 ? 'disabled' : ''}>Next →</button></div>`;
  $('#lib-q').addEventListener('input', e => { state.libQuery = e.target.value; state.libPage = 0; renderDataset(); });
  $('#lib-sort').addEventListener('change', e => { state.libSort = e.target.value; renderDataset(); });
  $('#lib-prev').addEventListener('click', () => { state.libPage--; renderDataset(); });
  $('#lib-next').addEventListener('click', () => { state.libPage++; renderDataset(); });
}

/* ---------------- PATIENTS ---------------- */
function renderPatients() {
  if (!state.patientDetail) {
    $('#patients-view').innerHTML = `<h2>Your synthetic cohort</h2>
      <p class="muted">Six fictional records for exploring the interface. No real patient data is accepted. Select a record for its full timeline.</p>
      <div class="patient-grid">${PATIENTS.map(p => `<button class="panel" data-patient="${p.id}" style="text-align:left;cursor:pointer"><div class="panel-pad">${patientHero(p)}</div></button>`).join('')}</div>`;
    $$('#patients-view [data-patient]').forEach(b => b.addEventListener('click', () => { state.patientDetail = b.dataset.patient; renderPatients(); }));
    return;
  }
  const p = PATIENTS.find(p => p.id === state.patientDetail);
  const events = [...p.encounters.map(e => ({ ...e, kind: '' })), ...p.conditions.map(c => ({ date: c.since, type: 'Diagnosis recorded', note: c.label, kind: '' })), ...p.medications.map(m => ({ date: m.start, type: 'Medication started', note: `${m.name} ${m.dose || ''}`, kind: '' }))]
    .sort((a, b) => b.date.localeCompare(a.date));
  $('#patients-view').innerHTML = `<button class="btn-sm" id="back-cohort">← All patients</button>
    <div class="patient-full" style="margin-top:16px"><div class="ph-top" style="display:flex;gap:14px;align-items:center;margin-bottom:8px">
      <div class="initials" style="width:52px;height:52px;background:#e2ebdd;border-radius:14px;display:grid;place-items:center;font-weight:700">${p.initials}</div>
      <div><h2 style="margin:0">${esc(p.name)} <span class="muted" style="font-weight:400;font-size:13px">${p.id}</span></h2>
      <p class="muted small" style="margin:2px 0 0">${p.age} years · ${p.sex} · Assessment ${fmtDate(ASSESSMENT)} · Fictional record</p></div></div>
      <h3>Conditions</h3><div>${p.conditions.map(c => `<span class="tag">${esc(c.label)}</span>`).join('') || '<p class="muted small">None recorded.</p>'}</div>
      <h3>Medications</h3>${p.medications.length ? `<table class="med-table"><thead><tr><th>Medication</th><th>Dose</th><th>Started</th><th>Status</th></tr></thead><tbody>
        ${p.medications.map(m => `<tr><td><b>${esc(m.name)}</b></td><td>${esc(m.dose || '—')}</td><td>${fmtDate(m.start)}</td><td>${m.end ? 'Ended ' + fmtDate(m.end) : '<span class="chip supported">Active</span>'}</td></tr>`).join('')}</tbody></table>` : '<p class="muted small">No medications recorded — expect unknowns where criteria need them.</p>'}
      <h3>Labs</h3>${p.labs.length ? `<table class="med-table"><thead><tr><th>Test</th><th>Value</th><th>Date</th></tr></thead><tbody>${p.labs.map(l => `<tr><td><b>${esc(l.name)}</b></td><td>${l.value} ${esc(l.unit)}</td><td>${fmtDate(l.date)}</td></tr>`).join('')}</tbody></table>` : '<p class="muted small">No lab results recorded.</p>'}
      <h3>Timeline</h3><div class="timeline">${events.map(e => `<div class="tl-item"><div class="tl-date">${fmtDate(e.date).toUpperCase()}</div><strong>${esc(e.type)}</strong><p>${esc(e.note)}</p></div>`).join('')}</div>
      <div class="divider"></div>
      <button class="button primary" id="screen-this">Screen ${esc(p.name)} in workspace <span aria-hidden="true">→</span></button></div>`;
  $('#back-cohort').addEventListener('click', () => { state.patientDetail = null; renderPatients(); });
  $('#screen-this').addEventListener('click', () => { state.patientId = p.id; state.selected = 0; switchView('screening'); });
}

/* ---------------- ACTIVITY ---------------- */
function renderActivity() {
  const items = Object.values(reviews).filter(r => r && r.reviewed).sort((a, b) => String(b.time).localeCompare(String(a.time)));
  const checks = Object.entries(checklist).filter(([, v]) => v && v.done).sort((a, b) => String(b[1].time).localeCompare(String(a[1].time)));
  $('#activity-view').innerHTML = `<h2>Local review history</h2>
    <p class="muted">Latest saved state per criterion, on this browser only. This is not an immutable audit log.</p>
    <h3>Criterion reviews (${items.length})</h3>
    ${items.map(r => `<div class="activity-item"><strong>${esc(r.patient)} / ${esc(r.trial)} / ${esc(r.criterion)}</strong><p>${esc(r.note || 'Reviewed without a note.')}</p><small>${esc(r.time)}</small></div>`).join('') || '<div class="empty">No reviews yet. Mark a criterion reviewed to see it here.</div>'}
    <h3>Checklist completions (${checks.length})</h3>
    ${checks.map(([k, v]) => `<div class="activity-item"><strong>${esc(k.replace('check:', '').replace(/:/g, ' / '))}</strong><p>${esc(v.note || 'Closed without a note.')}</p><small>${esc(v.time)}</small></div>`).join('') || '<p class="muted small">No checklist gaps closed yet.</p>'}
    <div class="divider"></div>
    <button class="button secondary" id="wipe-local">Clear local reviews & checklist</button>
    <p class="small muted">Removes everything stored in this browser for TrialLens.</p>`;
  $('#wipe-local').addEventListener('click', () => { if (!confirm('Clear all local reviews and checklist data?')) return; reviews = {}; checklist = {}; try { localStorage.removeItem('triallens-reviews-v1'); localStorage.removeItem('triallens-checklist-v1'); } catch {} renderActivity(); updateChecklistBadge(); toast('Local data cleared.'); });
}

/* ---------------- GUIDE ---------------- */
function renderGuide() {
  $('#guide-view').innerHTML = `<div class="guide"><h2>Evidence first. Judgment second.</h2>
    <p>This preview demonstrates the review experience using authored fixtures. It does not retrieve live trials, call an AI model, diagnose, or determine eligibility.</p>
    <div class="callout"><strong>The research question.</strong> Can explicit handling of missing information and temporal constraints reduce incorrect eligibility assertions compared with ordinary retrieval? Every <span class="chip unknown">Needs clarification</span> verdict and every <span class="temporal-flag">◷ temporal check</span> in this workspace is an instance of that question.</div>
    <h3>Read the criterion polarity</h3>
    <p><b>Supported</b> means the statement is supported by the record. For an <i>exclusion</i> criterion, a supported statement can be a reason to <i>exclude</i> — it is not evidence of eligibility. <b>Contradicted</b> and <b>unknown</b> are distinct: missing evidence must remain unknown, never quietly become a negative.</p>
    <h3>Temporal criteria</h3><p>Statements like “no admission within 30 days” are evaluated against dated encounters, not keyword presence. Open <b>Sam Ortiz → Blood pressure control study</b> to see an admission 45 days out correctly fall outside the window.</p>
    <h3>What works today</h3><ul>
    <li><b>Dashboard</b> — verdict distribution, unknowns by trial, review queue.</li>
    <li><b>Screening</b> — criterion-by-criterion evidence review with notes and JSON export.</li>
    <li><b>Compare</b> — one trial across the whole synthetic cohort.</li>
    <li><b>Checklist</b> — every unknown tracked to a next step.</li>
    <li><b>Report</b> — printable evidence-linked reviewer report.</li>
    <li><b>Trial library</b> — searchable historical snapshot (local import).</li></ul>
    <h3>Still to come</h3><p>Validated data contracts, public trial retrieval, the bounded investigation agent, expert-reviewed labels, secure persistence, and Azure deployment. See BACKLOG.md in the repository.</p></div>`;
}

/* ---------------- command palette ---------------- */
const COMMANDS = [
  { icon: '◈', title: 'Go to Dashboard', sub: 'Overview, charts, review queue', run: () => switchView('dashboard') },
  { icon: '▦', title: 'Go to Screening workspace', sub: 'Criterion-by-criterion review', run: () => switchView('screening') },
  { icon: '◫', title: 'Go to Case comparison', sub: 'One trial across patients', run: () => switchView('compare') },
  { icon: '☰', title: 'Go to Missing-info checklist', sub: 'Unknowns with next steps', run: () => switchView('checklist') },
  { icon: '⎙', title: 'Go to Reviewer report', sub: 'Printable evidence-linked report', run: () => switchView('report') },
  { icon: '▤', title: 'Go to Trial library', sub: 'Searchable historical snapshot', run: () => switchView('dataset') },
  { icon: '♙', title: 'Go to Synthetic patients', sub: 'Cohort timelines', run: () => switchView('patients') },
  { icon: '◐', title: 'Toggle dark mode', sub: 'Switch theme', run: () => toggleTheme() },
  { icon: '↓', title: 'Export current review (JSON)', sub: 'Download case + reviews', run: () => exportJSON() },
  { icon: '⎙', title: 'Print reviewer report', sub: 'Open report and print', run: () => { switchView('report'); setTimeout(() => window.print(), 350) } },
  ...PATIENTS.slice(0, 6).flatMap(p => TRIALS.slice(0, 2).map(t => ({ icon: '↗', title: `Load ${p.name} → ${t.id}`, sub: `${p.id} · ${t.title}`, run: () => { state.patientId = p.id; state.trialId = t.id; state.selected = 0; switchView('screening'); } }))),
];
let palIndex = 0;
function openPalette() { $('#palette-overlay').hidden = false; $('#palette-input').value = ''; renderPalette(''); setTimeout(() => $('#palette-input').focus(), 30); }
function closePalette() { $('#palette-overlay').hidden = true; }
function renderPalette(q) {
  const query = q.toLowerCase();
  const hits = COMMANDS.filter(c => `${c.title} ${c.sub}`.toLowerCase().includes(query)).slice(0, 12);
  palIndex = Math.min(palIndex, Math.max(0, hits.length - 1));
  $('#palette-list').innerHTML = hits.map((c, i) => `<button class="palette-item ${i === palIndex ? 'active' : ''}" role="option" aria-selected="${i === palIndex}" data-cmd="${COMMANDS.indexOf(c)}">
    <span class="p-ico">${c.icon}</span><span><b>${esc(c.title)}</b><small>${esc(c.sub)}</small></span></button>`).join('') || '<div class="empty">No matching command.</div>';
  $$('#palette-list .palette-item').forEach(b => b.addEventListener('click', () => { closePalette(); COMMANDS[Number(b.dataset.cmd)].run(); }));
}
function exportJSON() {
  const c = currentCase();
  const report = { schemaVersion: 1, mode: 'authored-synthetic-demo', clinicalDecision: false, patientId: c.patient.id, trialId: c.trial.id, exportedAt: new Date().toISOString(),
    criteria: c.criteria.map(x => ({ id: x.id, type: x.type, title: x.title, status: x.result.status, evidence: x.result.evidence, source: x.result.source, date: x.result.date, temporal: x.result.temporal, review: reviews[reviewKey(c.patient.id, c.trial.id, x.id)] || null })) };
  download(`triallens-${c.patient.id}-${c.trial.id}.json`, JSON.stringify(report, null, 2), 'application/json'); toast('Synthetic review exported.');
}

/* ---------------- theme ---------------- */
function setTheme(t) { document.documentElement.dataset.theme = t; try { localStorage.setItem('triallens-theme', t); } catch {} $('#theme-icon').textContent = t === 'dark' ? '◑' : '◐'; if (state.view === 'dashboard') renderDashboard(); }
function toggleTheme() { setTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'); toast(`Theme: ${document.documentElement.dataset.theme}.`); }

/* ---------------- view switching ---------------- */
const RENDER = { dashboard: renderDashboard, screening: renderScreening, compare: renderCompare, checklist: renderChecklist, report: renderReport, dataset: renderDataset, patients: renderPatients, activity: renderActivity, guide: renderGuide };
function switchView(view) {
  state.view = view;
  $$('.nav').forEach(b => b.classList.toggle('active', b.dataset.view === view));
  for (const v of Object.keys(RENDER)) $(`#${v}-view`).hidden = v !== view;
  const [title, sub] = VIEW_TITLES[view];
  $('#breadcrumb').textContent = title.replace(/\.$/, ''); $('#page-title').textContent = title; $('#page-subtitle').textContent = sub;
  $('#export').hidden = view !== 'screening'; $('#print-report').hidden = view !== 'report';
  RENDER[view]();
  $('#main').focus({ preventScroll: true });
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* ---------------- keyboard ---------------- */
const SHORTCUTS = [['Ctrl/⌘ + K', 'Command palette'], ['?', 'This shortcut list'], ['g then d', 'Dashboard'], ['g then s', 'Screening workspace'], ['g then c', 'Case comparison'], ['g then l', 'Missing-info checklist'], ['g then r', 'Reviewer report'], ['g then t', 'Trial library'], ['g then p', 'Synthetic patients'], ['/', 'Focus search (screening / library)'], ['j / k', 'Previous / next criterion'], ['t', 'Toggle dark mode'], ['Esc', 'Close dialogs']];
let gPending = false;
document.addEventListener('keydown', e => {
  const inField = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName);
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); $('#palette-overlay').hidden ? openPalette() : closePalette(); return; }
  if (e.key === 'Escape') { closePalette(); $('#shortcuts-overlay').hidden = true; return; }
  if (inField) return;
  if (e.key === '?') { $('#shortcuts-overlay').hidden = false; return; }
  if (e.key === '/') { e.preventDefault(); const s = $('#search') || $('#lib-q'); if (s) s.focus(); return; }
  if (e.key === 't' && !gPending) { toggleTheme(); return; }
  if (gPending) { gPending = false; const m = { d: 'dashboard', s: 'screening', c: 'compare', l: 'checklist', r: 'report', t: 'dataset', p: 'patients' }; if (m[e.key]) switchView(m[e.key]); return; }
  if (e.key === 'g') { gPending = true; setTimeout(() => gPending = false, 900); return; }
  if (state.view === 'screening' && (e.key === 'j' || e.key === 'k')) {
    const vis = filteredCriteria(); if (!vis.length) return;
    let i = vis.findIndex(x => x.index === state.selected);
    i = e.key === 'j' ? Math.min(vis.length - 1, i + 1) : Math.max(0, i - 1);
    state.selected = vis[i].index; renderCriteriaList(); renderDetail();
    $(`#criteria-list [data-index="${state.selected}"]`)?.scrollIntoView({ block: 'nearest' });
  }
});

/* ---------------- init ---------------- */
function init() {
  setTheme(store.get('triallens-theme', 'light'));
  $('#shortcuts-list').innerHTML = SHORTCUTS.map(([k, d]) => `<dt><kbd>${esc(k)}</kbd></dt><dd>${esc(d)}</dd>`).join('');
  $('#shortcuts-close').addEventListener('click', () => $('#shortcuts-overlay').hidden = true);
  $('#palette-btn').addEventListener('click', openPalette);
  $('#palette-overlay').addEventListener('click', e => { if (e.target.id === 'palette-overlay') closePalette(); });
  $('#palette-input').addEventListener('input', e => { palIndex = 0; renderPalette(e.target.value); });
  $('#palette-input').addEventListener('keydown', e => {
    const items = $$('#palette-list .palette-item'); if (!items.length) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); palIndex = (palIndex + 1) % items.length; renderPalette($('#palette-input').value); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); palIndex = (palIndex - 1 + items.length) % items.length; renderPalette($('#palette-input').value); }
    else if (e.key === 'Enter') { e.preventDefault(); items[palIndex]?.click(); }
  });
  $('#theme-btn').addEventListener('click', toggleTheme);
  $('#brand-home').addEventListener('click', e => { e.preventDefault(); switchView('dashboard'); });
  $$('.nav').forEach(b => b.addEventListener('click', () => switchView(b.dataset.view)));
  $('#export').addEventListener('click', exportJSON);
  $('#print-report').addEventListener('click', () => window.print());
  updateChecklistBadge();
  switchView('dashboard');
  $('#env-badge').textContent = 'ENG preview';
}
document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', init) : init();
