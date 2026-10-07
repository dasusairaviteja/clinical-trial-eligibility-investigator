"""Reproducible control-regression study, NOT an LLM or clinical experiment."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
from .comparison import compare
from .data_adapters import synthetic_source
from .experiments import run_arm
from .registry import registry_from_json

# Labels express the intended synthetic rule semantics, not expert annotation.
CASES = (
    ('recent_event',['2026-09-01'],None,None,'supported'),
    ('old_event',['2025-01-01'],'2026-04-06','2026-10-06','contradicted'),
    ('future_event',['2027-01-01'],'2026-04-06','2026-10-06','contradicted'),
    ('missing_history',[],None,None,'unknown'),
    ('partial_history',[],'2026-07-01','2026-10-06','unknown'),
    ('complete_absence',[],'2026-04-06','2026-10-06','contradicted'),
)


def scripted_planner(instructions, observations):
    """Deterministic planner fixture; never receives expected labels."""
    if not observations:return {'tool':'check','arguments':{'criterion_id':'event'}}
    if len(observations)==1:return {'tool':'submit','arguments':observations[0]['result']}
    return {'tool':'finish','arguments':{}}


def run_study():
    arms=('bounded_agent','without_temporal','without_missing_evidence_control')
    predictions={arm:[] for arm in arms}
    for name,events,lower,upper,gold in CASES:
        patient,trial='SYN-'+name,'SYN-TRIAL-'+name
        source=synthetic_source({'schema':'synthetic-observation-v1','patient_id':patient,
            'source_id':'history','version':'v1','type':'event_history','name':'stroke',
            'events':events,'complete_since':lower,'complete_through':upper},synthetic_attested=True)
        registry=registry_from_json(json.dumps({'schema_version':1,'sources':[asdict(source)],
            'trials':[{'trial_id':trial,'version':'v1','criteria':[{'criterion_id':'event',
            'trial_id':trial,'kind':'exclusion','statement':'Event stroke within 6 months before 2026-10-06'}]}]}).encode())
        request={'case_id':name,'patient_id':patient,'trial_ref':{'trial_id':trial,'trial_version':'v1'},
                 'source_refs':[{'source_id':'history','source_version':'v1'}]}
        for arm in arms:
            result=run_arm(arm,registry,request,scripted_planner)
            finding=result['report']['criteria'][0]
            predictions[arm].append({'patient_id':patient,'trial_id':trial,'criterion_id':'event',
                'kind':'exclusion','gold':gold,'predicted':finding['verdict'],
                'evidence_correct':finding['verdict']==gold,
                'latency_ms':result['latency_ms'],'cost_usd':0})
    return {'study_type':'synthetic_control_regression_with_scripted_planner',
        'label_source':'authored_fixture_expectations_not_clinical_adjudication',
        'evidence_correct_definition':'fixture label agreement only; not expert evidence accuracy',
        'fixture_sha256':hashlib.sha256(json.dumps(CASES).encode()).hexdigest(),
        'seed':42,'model_calls':0,'predictions':predictions,
        'comparisons':{arm:compare(predictions[arm],predictions['bounded_agent']) for arm in arms[1:]},
        'limitations':'Engineered fixtures test controls. No LLM, clinical efficacy, novelty or publication evidence.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    result=run_study()
    with args.output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
