"""Offline, review-gated adapters. Inputs must be synthetic or licensed public data."""
from datetime import date
import hashlib
import json
from .ingestion import parse_criteria
from .contracts import SourceDocument
from .registry import registry_from_json


def public_trial_candidate(record):
    """Map a supplied ClinicalTrials.gov v2 study JSON; performs no network request."""
    protocol = record['protocolSection']
    identifier = protocol['identificationModule']['nctId']
    updated = protocol['statusModule']['lastUpdatePostDateStruct']['date']
    text = protocol['eligibilityModule']['eligibilityCriteria']
    candidate = parse_criteria(identifier,updated,text)
    candidate['raw_text'] = text
    candidate['record_sha256'] = hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()
    return candidate


def promote_candidate(candidate, reviewer, approved_ids):
    """Explicit approval is required; reparse trusted offsets before promotion."""
    if not isinstance(reviewer,str) or not reviewer.strip():
        raise ValueError('reviewer required')
    rebuilt = parse_criteria(candidate['trial_id'],candidate['updated'],candidate['raw_text'])
    if any(candidate.get(key) != rebuilt[key] for key in rebuilt):
        raise ValueError('candidate changed; re-review required')
    expected = [row['criterion_id'] for row in rebuilt['criteria']]
    if rebuilt['issues'] or not expected or approved_ids != expected:
        raise ValueError('all parsed criteria must be reviewed and unparsed text resolved')
    trial = {'trial_id':candidate['trial_id'],'version':candidate['updated']+':'+candidate['source_sha256'][:16],
             'criteria':[{k:row[k] for k in ('criterion_id','trial_id','kind','statement')} for row in rebuilt['criteria']]}
    registry_from_json(json.dumps({'schema_version':1,'sources':[],'trials':[trial]}).encode())
    return {'trial':trial,'approval':{'reviewer':reviewer,'source_sha256':candidate['source_sha256'],'approved_ids':approved_ids}}


def synthetic_source(record, *, synthetic_attested=False):
    """Validate the project's small synthetic observation format, not arbitrary FHIR."""
    if synthetic_attested is not True or record.get('schema') != 'synthetic-observation-v1':
        raise ValueError('explicit synthetic provenance attestation required')
    base = {'schema','patient_id','source_id','version','type','name'}
    if record.get('type') == 'measurement':
        if set(record) != base | {'date','value','unit'}: raise ValueError('measurement fields')
        date.fromisoformat(record['date'])
        from decimal import Decimal
        if not isinstance(record['value'],str) or not Decimal(record['value']).is_finite():
            raise ValueError('finite decimal text required')
        if not isinstance(record['unit'],str) or not record['unit']: raise ValueError('unit required')
    elif record.get('type') == 'event_history':
        if set(record) != base | {'events','complete_since','complete_through'}: raise ValueError('event fields')
        if not isinstance(record['events'],list) or len(record['events']) > 1000: raise ValueError('event list')
        for value in record['events']: date.fromisoformat(value)
        lower,upper = record['complete_since'],record['complete_through']
        if (lower is None) != (upper is None): raise ValueError('coverage needs both endpoints')
        if lower is not None and date.fromisoformat(lower) > date.fromisoformat(upper): raise ValueError('reversed coverage')
    else: raise ValueError('unsupported observation')
    for key in base:
        if not isinstance(record[key],str) or not record[key].strip(): raise ValueError('text fields required')
    text = json.dumps(record,sort_keys=True,allow_nan=False)
    if len(text) > 100_000: raise ValueError('observation too large')
    return SourceDocument(record['source_id'],record['patient_id'],record['version'],text)
