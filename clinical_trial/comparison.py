"""Paired criterion comparisons with patient-cluster bootstrap uncertainty."""
import argparse
import hashlib
import json
from pathlib import Path
import random
from .evaluation import evaluate
from .experiments import paired_predictions


def identity(row):
    return row['patient_id'], row['trial_id'], row['criterion_id']


def outcomes(rows):
    """Unconditional errors per criterion and coverage avoid a changing denominator."""
    count = len(rows)
    return {
        'accuracy':sum(r['gold']==r['predicted'] for r in rows)/count,
        'coverage':sum(r['predicted']!='unknown' for r in rows)/count,
        'false_no_barrier_per_criterion':sum(
            (r['kind'],r['predicted']) in (('inclusion','supported'),('exclusion','contradicted'))
            and r['gold']!=r['predicted'] for r in rows)/count,
    }


def compare(reference, candidate, *, seed=42, repetitions=1000):
    if type(seed) is not int or type(repetitions) is not int or not 100<=repetitions<=10000:
        raise ValueError('integer seed and 100..10000 repetitions required')
    # Validate label, evidence adjudication, cost and latency fields first.
    reference_metrics,candidate_metrics = evaluate(reference),evaluate(candidate)
    paired_predictions({'reference':reference,'candidate':candidate})
    candidate_by_id = {identity(r):r for r in candidate}
    pairs = [(r,candidate_by_id[identity(r)]) for r in sorted(reference,key=identity)]
    for a,b in pairs:
        if (a['gold'],a['kind']) != (b['gold'],b['kind']):
            raise ValueError('paired labels and polarity must agree')
    def delta(sample):
        a,b = outcomes([p[0] for p in sample]),outcomes([p[1] for p in sample])
        return {key:b[key]-a[key] for key in a}
    differences = delta(pairs)
    groups = {}
    for pair in pairs: groups.setdefault(pair[0]['patient_id'],[]).append(pair)
    intervals = None
    if len(groups)>=2:
        rng,patients = random.Random(seed),sorted(groups)
        samples = {key:[] for key in differences}
        for _ in range(repetitions):
            sample = [pair for p in rng.choices(patients,k=len(patients)) for pair in groups[p]]
            for key,value in delta(sample).items(): samples[key].append(value)
        intervals = {}
        for key,values in samples.items():
            values.sort()
            intervals[key] = [values[int(.025*repetitions)],values[min(int(.975*repetitions),repetitions-1)]]
    return {'direction':'candidate_minus_reference','paired_criteria':len(pairs),
            'patient_clusters':len(groups),'reference':reference_metrics,'candidate':candidate_metrics,
            'delta':differences,'patient_bootstrap_95pct':intervals,'seed':seed,'repetitions':repetitions,
            'limitations':'Patient clustering does not model shared-trial dependence; no causal or clinical claim.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference',type=Path)
    parser.add_argument('candidate',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--seed',type=int,default=42)
    args=parser.parse_args()
    raw_a,raw_b=args.reference.read_bytes(),args.candidate.read_bytes()
    result=compare(json.loads(raw_a),json.loads(raw_b),seed=args.seed)
    result['input_sha256']=[hashlib.sha256(raw).hexdigest() for raw in (raw_a,raw_b)]
    with args.output.open('x') as stream: json.dump(result,stream,indent=2,allow_nan=False)


if __name__=='__main__':main()
