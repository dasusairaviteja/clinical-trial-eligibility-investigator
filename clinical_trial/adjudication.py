"""Arm-blinded review packets and exact reviewer-attributed result joins.

Blinding is procedural, not cryptographic. Keep the key separate from reviewers.
The application cannot certify that a reviewer has clinical qualifications.
"""
import hashlib
import random
import copy
import argparse
import json
from pathlib import Path

from .cohort import digest
from .dataset import join_adjudication
from .evaluation import evaluate


def review_packet(cohort, seed=42):
    if type(seed) is not int:
        raise ValueError('integer seed required')
    rows, mapping = [], {}
    for arm, runs in cohort['runs'].items():
        for run in runs:
            report = run['report']
            for criterion in report['criteria']:
                identity = (report['patient_id'], report['trial_id'], criterion['criterion_id'])
                review_id = hashlib.sha256(repr((seed, arm, identity)).encode()).hexdigest()
                if review_id in mapping:
                    raise ValueError('duplicate review identity')
                mapping[review_id] = {'arm': arm, 'identity': identity,
                                      'criterion_sha256': digest(criterion)}
                rows.append({'review_id': review_id, 'patient_id': identity[0], 'trial_id': identity[1],
                             'criterion': copy.deepcopy(criterion), 'gold': None, 'evidence_correct': None,
                             'reviewer': '', 'rationale': ''})
    if not rows:
        raise ValueError('empty review packet')
    random.Random(seed).shuffle(rows)
    return {'status': 'requires_independent_review', 'rows': rows}, {
        'cohort_sha256': digest(cohort), 'mapping': mapping, 'seed': seed}


def score_review(cohort, key, completed):
    if key['cohort_sha256'] != digest(cohort):
        raise ValueError('cohort changed after blinding')
    rows = completed['rows']
    ids = [r['review_id'] for r in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(key['mapping']):
        raise ValueError('review must cover every exact packet item once')
    annotations = {arm: [] for arm in cohort['predictions']}
    gold_by_identity = {}
    for row in rows:
        entry = key['mapping'][row['review_id']]
        patient, trial, criterion = entry['identity']
        if (row['patient_id'], row['trial_id'], row['criterion']['criterion_id']) != (patient, trial, criterion):
            raise ValueError('review identity changed')
        if digest(row['criterion']) != entry['criterion_sha256']:
            raise ValueError('reviewed evidence changed')
        identity = (patient, trial, criterion)
        if identity in gold_by_identity and gold_by_identity[identity] != row['gold']:
            raise ValueError('gold disagreement across arms requires adjudication')
        gold_by_identity[identity] = row['gold']
        if not isinstance(row.get('rationale'), str) or not row['rationale'].strip():
            raise ValueError('review rationale required')
        annotations[entry['arm']].append({'patient_id': patient, 'trial_id': trial,
            'criterion_id': criterion, 'kind': row['criterion']['kind'], 'gold': row['gold'],
            'evidence_correct': row['evidence_correct'], 'reviewer': row['reviewer']})
    return {arm: evaluate(join_adjudication(predictions, annotations[arm]))
            for arm, predictions in cohort['predictions'].items()}


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
        with args.key.open('x') as stream:
            json.dump(key, stream, indent=2)
        args.key.chmod(0o600)
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
