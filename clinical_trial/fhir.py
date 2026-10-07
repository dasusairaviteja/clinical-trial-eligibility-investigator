"""Conservative adapter for synthetic FHIR R4 quantitative Observations.

Requires an operator-approved coding map; does not infer clinical equivalence.
Unmapped/unsupported resources are reported, never silently made into evidence.
"""
from datetime import date,datetime
import hashlib
import json
from .data_adapters import synthetic_source


def observations(bundle, patient_id, coding_map, *, synthetic_attested=False):
    if synthetic_attested is not True or bundle.get('resourceType')!='Bundle':
        raise ValueError('synthetic Bundle required')
    entries=bundle.get('entry')
    if not isinstance(entries,list) or len(entries)>10000:
        raise ValueError('bounded entry list required')
    patients=[e.get('resource',{}) for e in entries if e.get('resource',{}).get('resourceType')=='Patient']
    if len(patients)!=1 or patients[0].get('id')!=patient_id:
        raise ValueError('exactly one matching synthetic patient required')
    patient_refs={'Patient/'+patient_id}
    patient_refs.update(e['fullUrl'] for e in entries if e.get('resource',{}).get('resourceType')=='Patient' and e.get('fullUrl'))
    sources,issues,seen=[],[],set()
    for index,entry in enumerate(entries):
        resource=entry.get('resource',{})
        if resource.get('resourceType')=='Patient':continue
        if resource.get('resourceType')!='Observation':
            issues.append({'index':index,'code':'unsupported_resource'});continue
        try:
            if resource.get('subject',{}).get('reference') not in patient_refs:
                raise ValueError('wrong_patient')
            if resource.get('status') not in ('final','amended','corrected'):
                raise ValueError('nonfinal_observation')
            if resource.get('modifierExtension') or resource.get('component') or resource.get('dataAbsentReason'):
                raise ValueError('unsupported_observation_semantics')
            mappings={coding_map[(c.get('system'),c.get('code'))] for c in resource.get('code',{}).get('coding',[])
                      if (c.get('system'),c.get('code')) in coding_map}
            if len(mappings)!=1:raise ValueError('unmapped_or_ambiguous_code')
            name,unit=next(iter(mappings))
            quantity=resource['valueQuantity']
            if quantity.get('comparator') or quantity.get('system')!='http://unitsofmeasure.org' or quantity.get('code')!=unit:
                raise ValueError('unsupported_quantity')
            raw_date=resource['effectiveDateTime']
            # Retain the assessment's explicitly recorded calendar date; no UTC
            # conversion. Partial dates and timezone-less timestamps are rejected.
            if len(raw_date)==10:day=date.fromisoformat(raw_date).isoformat()
            else:
                stamp=datetime.fromisoformat(raw_date.replace('Z','+00:00'))
                if stamp.tzinfo is None:raise ValueError('timezone_required')
                day=stamp.date().isoformat()
            identifier=resource['id']
            version=resource.get('meta',{}).get('versionId') or hashlib.sha256(json.dumps(resource,sort_keys=True).encode()).hexdigest()
            key=(identifier,version)
            if key in seen:raise ValueError('duplicate_observation')
            seen.add(key)
            value=quantity['value']
            if type(value) not in (int,float):raise ValueError('numeric_value_required')
            sources.append(synthetic_source({'schema':'synthetic-observation-v1','patient_id':patient_id,
                'source_id':'fhir-'+identifier,'version':version,'type':'measurement','name':name,
                'date':day,'value':str(value),'unit':unit},synthetic_attested=True))
        except (KeyError,TypeError,ValueError):
            issues.append({'index':index,'code':'observation_requires_review'})
    return {'sources':sources,'issues':issues,'status':'operator_review_required',
            'input_sha256':hashlib.sha256(json.dumps(bundle,sort_keys=True,allow_nan=False).encode()).hexdigest()}
