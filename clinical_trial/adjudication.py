"""Arm-blinded review packets and exact reviewer-attributed result joins.

Blinding is procedural, not cryptographic. Keep the key separate from reviewers.
The application cannot certify that a reviewer has clinical qualifications.
"""
import hashlib
import random
import copy
import argparse
import json
import os
from pathlib import Path

from .cohort import digest
from .dataset import join_adjudication
from .evaluation import evaluate


def review_packet(cohort, seed=42):
    if type(seed) is not int:
        raise ValueError('integer seed required')
    gold_rows, evidence_rows, mapping, gold_seen = [], [], {}, set()
    for arm, runs in cohort['runs'].items():
        for run in runs:
            report = run['report']
            for criterion in report['criteria']:
                identity = (report['patient_id'], report['trial_id'], criterion['criterion_id'])
                definition = {name: criterion[name] for name in ('criterion_id', 'kind', 'statement')}
                if identity not in gold_seen:
                    review_id = hashlib.sha256(repr((seed, 'gold', identity)).encode()).hexdigest()
                    mapping[review_id] = {'task': 'gold', 'identity': identity,
                                          'criterion_sha256': digest(definition)}
                    gold_rows.append({'review_id': review_id, 'patient_id': identity[0],
                        'trial_id': identity[1], 'criterion': definition, 'gold': None,
                        'reviewer': '', 'rationale': ''})
                    gold_seen.add(identity)
                review_id = hashlib.sha256(repr((seed, 'evidence', arm, identity)).encode()).hexdigest()
                mapping[review_id] = {'task': 'evidence', 'arm': arm, 'identity': identity,
                                      'criterion_sha256': digest(criterion)}
                evidence_rows.append({'review_id': review_id, 'patient_id': identity[0],
                    'trial_id': identity[1], 'candidate_output': copy.deepcopy(criterion),
                    'evidence_correct': None, 'reviewer': '', 'rationale': ''})
    if not gold_rows or not evidence_rows:
        raise ValueError('empty review packet')
    random.Random(seed).shuffle(gold_rows)
    random.Random(seed + 1).shuffle(evidence_rows)
    return {'schema_version': 2, 'status': 'requires_independent_review',
            'instructions': {'gold_rows': 'Judge eligibility truth without seeing model outputs.',
                             'evidence_rows': 'Judge only whether the displayed output evidence supports its prediction.'},
            'gold_rows': gold_rows, 'evidence_rows': evidence_rows}, {
        'cohort_sha256': digest(cohort), 'mapping': mapping, 'seed': seed}


def score_review(cohort, key, completed):
    if key['cohort_sha256'] != digest(cohort):
        raise ValueError('cohort changed after blinding')
    if completed.get('schema_version') != 2:
        raise ValueError('unsupported review packet schema')
    rows = completed.get('gold_rows', []) + completed.get('evidence_rows', [])
    ids = [r['review_id'] for r in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(key['mapping']):
        raise ValueError('review must cover every exact packet item once')
    gold_by_identity, evidence_by_arm_identity = {}, {}
    for row in rows:
        entry = key['mapping'][row['review_id']]
        patient, trial, criterion = entry['identity']
        candidate = row['criterion'] if entry['task'] == 'gold' else row['candidate_output']
        if (row['patient_id'], row['trial_id'], candidate['criterion_id']) != (patient, trial, criterion):
            raise ValueError('review identity changed')
        if digest(candidate) != entry['criterion_sha256']:
            raise ValueError('reviewed evidence changed')
        if not isinstance(row.get('rationale'), str) or not row['rationale'].strip():
            raise ValueError('review rationale required')
        if not isinstance(row.get('reviewer'), str) or not row['reviewer'].strip():
            raise ValueError('named reviewer required')
        identity = (patient, trial, criterion)
        if entry['task'] == 'gold':
            gold_by_identity[identity] = row['gold']
        else:
            evidence_by_arm_identity[(entry['arm'], identity)] = (
                row['evidence_correct'], row['reviewer'])
    annotations = {arm: [] for arm in cohort['predictions']}
    for arm, predictions in cohort['predictions'].items():
        for prediction in predictions:
            identity = (prediction['patient_id'], prediction['trial_id'], prediction['criterion_id'])
            evidence_correct, reviewer = evidence_by_arm_identity[(arm, identity)]
            annotations[arm].append({**{name: prediction[name] for name in
                ('patient_id', 'trial_id', 'criterion_id', 'kind')},
                'gold': gold_by_identity[identity], 'evidence_correct': evidence_correct,
                'reviewer': reviewer})
    return {arm: evaluate(join_adjudication(predictions, annotations[arm]))
            for arm, predictions in cohort['predictions'].items()}


def write_private_key(path, key):
    """Create an owner-only mapping without exposing a permissive write window."""
    encoded = json.dumps(key, indent=2, allow_nan=False)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(encoded)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'score'])
    parser.add_argument('cohort', type=Path)
    parser.add_argument('packet', type=Path)
    parser.add_argument('key', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    cohort = json.loads(args.cohort.read_bytes())
    if args.action == 'prepare':
        if args.packet.exists() or args.key.exists() or args.packet.resolve() == args.key.resolve():
            parser.error('packet and private key need different unused paths')
        packet, key = review_packet(cohort)
        write_private_key(args.key, key)
        with args.packet.open('x') as stream:
            json.dump(packet, stream, indent=2)
    else:
        if args.output is None:
            parser.error('score requires --output')
        result = score_review(cohort, json.loads(args.key.read_bytes()), json.loads(args.packet.read_bytes()))
        encoded = json.dumps(result, indent=2, allow_nan=False)
        with args.output.open('x') as stream:
            stream.write(encoded)


if __name__ == '__main__':
    main()
