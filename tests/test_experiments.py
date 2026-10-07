import json
from pathlib import Path
import unittest
from clinical_trial.experiments import run_arm, paired_predictions, BudgetedPlanner
from clinical_trial.registry import registry_from_json

ROOT=Path(__file__).resolve().parents[1]


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.registry=registry_from_json((ROOT/'examples/synthetic_sources.json').read_bytes())
        self.request=json.loads((ROOT/'examples/synthetic_request.json').read_text())
        self.request.pop('schema_version');self.request.pop('findings')

    def test_rules_run_requires_no_provider(self):
        result=run_arm('rules',self.registry,self.request)
        self.assertEqual(result['model_calls'],0)
        self.assertEqual(result['cost_usd'],0)
        self.assertEqual(result['report']['criteria'][0]['verdict'],'supported')

    def test_rag_never_receives_gold_labels_and_stops_at_cap(self):
        seen=[]
        def planner(instructions,evidence):
            seen.append(instructions)
            return {'tool':'submit','arguments':{'criterion_id':instructions['criterion_id'],
                    'verdict':'unknown','citations':[],'missing_information':['Review needed']}}
        result=run_arm('standard_rag',self.registry,self.request,planner,calls=1)
        self.assertEqual(result['model_calls'],1)
        self.assertEqual(len(seen),1)
        self.assertNotIn('gold',json.dumps(seen))
        self.assertEqual(len(result['report']['criteria']),2)
        self.assertIsNone(result['cost_usd'])

    def test_uncontrolled_arm_still_has_operational_caps(self):
        planner=lambda *_:{'tool':'retrieve','arguments':{'query':'Age'}}
        for arm in ('uncontrolled_agent','bounded_agent'):
            result=run_arm(arm,self.registry,self.request,planner,calls=2)
            self.assertEqual(result['model_calls'],2)

    def test_comparisons_reject_missing_and_duplicate_predictions(self):
        row={'patient_id':'p','trial_id':'t','criterion_id':'c'}
        self.assertTrue(paired_predictions({'a':[row],'b':[row]}))
        for arms in ({'a':[row],'b':[]},{'a':[row,row]}):
            with self.assertRaises(ValueError):paired_predictions(arms)

    def test_context_limit_prevents_provider_call(self):
        def fail(*args):raise AssertionError('provider must not run')
        with self.assertRaises(RuntimeError):BudgetedPlanner(fail,context_bytes=10)({'long':'x'*100},[])
