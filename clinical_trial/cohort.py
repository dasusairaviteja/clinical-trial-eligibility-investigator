"""Run a frozen request cohort under identical arm-level resource ceilings."""
import argparse
import hashlib
import json
from pathlib import Path

from .experiments import ARMS, BASELINE_PROMPT, run_arm, paired_predictions
from .registry import registry_from_json, TrialReference, SourceReference
from .report import _unique_object, _reject_constant
from .contracts import require_text


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def run_cohort(registry, requests, arms=('rules',), *, planner_factory=None,
               calls=8, context_bytes=50000, planner_provenance='none'):
    if (not isinstance(requests, list) or not 1 <= len(requests) <= 1000 or
            not arms or len(set(arms)) != len(arms) or any(arm not in ARMS for arm in arms)):
        raise ValueError('invalid cohort or arms')
    if type(calls) is not int or not 1 <= calls <= 20 or type(context_bytes) is not int or not 100 <= context_bytes <= 100000:
        raise ValueError('invalid resource limits')
    if any(arm != 'rules' for arm in arms) and (planner_factory is None or planner_provenance == 'none'):
        raise ValueError('planner factory and provenance required for model arms')
    require_text(planner_provenance, 'planner provenance')
    # Preflight every reference before any planner can incur cost.
    identities = set()
    for request in requests:
        if set(request) != {'case_id', 'patient_id', 'trial_ref', 'source_refs'}:
            raise ValueError('invalid request fields')
        require_text(request['case_id'], 'case_id')
        require_text(request['patient_id'], 'patient_id')
        trial = registry.resolve_trial(TrialReference(**request['trial_ref']))
        registry.resolve_sources(request['patient_id'], tuple(SourceReference(**r) for r in request['source_refs']))
        for criterion in trial.criteria:
            identity = (request['patient_id'], trial.trial_id, criterion.criterion_id)
            if identity in identities:
                raise ValueError('duplicate patient/trial/criterion in cohort')
            identities.add(identity)
    runs, predictions = {arm: [] for arm in arms}, {arm: [] for arm in arms}
    for request in requests:
        for arm in arms:
            planner = None if arm == 'rules' else planner_factory(arm)
            result = run_arm(arm, registry, request, planner, calls, context_bytes)
            runs[arm].append(result)
            count = len(result['report']['criteria'])
            for criterion in result['report']['criteria']:
                predictions[arm].append({'patient_id': request['patient_id'],
                    'trial_id': result['report']['trial_id'], 'criterion_id': criterion['criterion_id'],
                    'kind': criterion['kind'], 'predicted': criterion['verdict'],
                    # Allocate case-level totals equally; preserve originals in runs.
                    'latency_ms': result['latency_ms'] / count,
                    'cost_usd': None if result['cost_usd'] is None else result['cost_usd'] / count})
    paired_predictions(predictions)
    return {'schema_version': 1, 'request_sha256': digest(requests),
            'planner_provenance': planner_provenance, 'runs': runs, 'predictions': predictions,
            'budget': {'calls_per_case': calls, 'context_bytes_per_call': context_bytes},
            'resource_accounting': 'equal ceilings, not matched actual token consumption',
            'status': 'unadjudicated_no_research_conclusions'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('registry', type=Path)
    parser.add_argument('requests', type=Path, help='JSON array of trusted requests')
    parser.add_argument('output', type=Path)
    parser.add_argument('--arms', nargs='+', choices=ARMS, default=['rules'])
    parser.add_argument('--allow-paid-model', action='store_true')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists')
    registry_raw = args.registry.read_bytes()
    if args.requests.stat().st_size > 1_000_000:
        parser.error('request input exceeds size limit')
    requests = json.loads(args.requests.read_bytes(), object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    factory = None
    if any(arm != 'rules' for arm in args.arms):
        if not args.allow_paid_model:
            parser.error('paid model arms require explicit opt-in')
        from .azure_planner import AzurePlanner
        def factory(arm):
            planner = AzurePlanner.from_environment()
            if arm in ('standard_rag', 'uncontrolled_agent'):
                planner.system_prompt = BASELINE_PROMPT
            return planner
    result = run_cohort(registry_from_json(registry_raw), requests, args.arms,
                        planner_factory=factory, planner_provenance='azure_live' if factory else 'none')
    result['registry_sha256'] = hashlib.sha256(registry_raw).hexdigest()
    encoded = json.dumps(result, indent=2, allow_nan=False)
    with args.output.open('x') as stream:
        stream.write(encoded)


if __name__ == '__main__':
    main()
