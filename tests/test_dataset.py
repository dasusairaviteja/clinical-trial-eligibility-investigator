import unittest
from clinical_trial.dataset import split_components,join_adjudication
from clinical_trial.evaluation import validate_disjoint


class DatasetTests(unittest.TestCase):
    def test_connected_patients_and_trials_never_cross_splits(self):
        rows=[{'patient_id':p,'trial_id':t,'criterion_id':'c'} for p,t in [('p1','t1'),('p2','t1'),('p2','t2'),('p3','t3')]]
        result=split_components(rows)
        self.assertEqual(result,split_components(list(reversed(rows))))
        validate_disjoint(result['splits'])
        self.assertEqual(result['components'],2)

    def test_adjudication_requires_exact_blinded_alignment(self):
        prediction={'patient_id':'p','trial_id':'t','criterion_id':'c','kind':'inclusion',
                    'predicted':'unknown','latency_ms':1,'cost_usd':0}
        label={k:prediction[k] for k in ('patient_id','trial_id','criterion_id','kind')}
        label.update(gold='unknown',evidence_correct=True,reviewer='expert-fixture')
        self.assertEqual(join_adjudication([prediction],[label])[0]['gold'],'unknown')
        for bad in [[],[{**label,'reviewer':''}],[{**label,'kind':'exclusion'}]]:
            with self.assertRaises(ValueError):join_adjudication([prediction],bad)
