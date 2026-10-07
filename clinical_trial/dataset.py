"""Deterministic patient/trial component splits and explicit annotation joins."""
import hashlib
from .evaluation import evaluate,validate_disjoint


def key(row):return row['patient_id'],row['trial_id'],row['criterion_id']


def split_components(rows, seed=42):
    if not rows or type(seed) is not int:raise ValueError('nonempty dataset and integer seed required')
    parents={}
    def find(node):
        parents.setdefault(node,node)
        while parents[node]!=node:
            parents[node]=parents[parents[node]];node=parents[node]
        return node
    for row in rows:
        a,b=find('patient:'+row['patient_id']),find('trial:'+row['trial_id'])
        parents[max(a,b)]=min(a,b)
    groups={}
    for row in rows:groups.setdefault(find('patient:'+row['patient_id']),[]).append(row)
    result={'train':[],'validation':[],'test':[]}
    for root,group in sorted(groups.items()):
        bucket=int(hashlib.sha256(f'{seed}:{root}'.encode()).hexdigest(),16)%10
        partition='train' if bucket<6 else ('validation' if bucket<8 else 'test')
        result[partition].extend(sorted(group,key=key))
    validate_disjoint(result)
    return {'splits':result,'components':len(groups),'seed':seed,
            'warnings':[name+' is empty; collect more independent groups' for name,values in result.items() if not values]}


def join_adjudication(predictions,annotations):
    if len({key(r) for r in predictions})!=len(predictions) or len({key(r) for r in annotations})!=len(annotations):
        raise ValueError('duplicate criterion identities')
    labels={key(r):r for r in annotations}
    if set(labels)!={key(r) for r in predictions}:raise ValueError('annotations must cover exact predictions')
    joined=[]
    for prediction in predictions:
        label=labels[key(prediction)]
        if not isinstance(label.get('reviewer'),str) or not label['reviewer'].strip():raise ValueError('named adjudicator required')
        if label['kind']!=prediction['kind']:raise ValueError('criterion polarity mismatch')
        if 'gold' in prediction or 'evidence_correct' in prediction:raise ValueError('predictions must not contain labels')
        joined.append({**prediction,'gold':label['gold'],'evidence_correct':label['evidence_correct']})
    evaluate(joined)
    return joined
