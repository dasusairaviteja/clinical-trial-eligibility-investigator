import json
from pathlib import Path
import unittest
from clinical_trial.agent import run_agent
from clinical_trial.registry import registry_from_json

ROOT = Path(__file__).resolve().parents[1]


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.registry = registry_from_json((ROOT/'examples/synthetic_sources.json').read_bytes())
        self.request = json.loads((ROOT/'examples/synthetic_request.json').read_text())
        self.request.pop('schema_version')
        self.findings = self.request.pop('findings')

    def test_planner_retrieves_and_submits_cited_finding(self):
        self.findings[0]['citations'][0].update(end=14,quote='Age: 54 years.')
        actions = iter([{'tool':'retrieve','arguments':{'query':'Age'}},
                        {'tool':'submit','arguments':self.findings[0]},
                        {'tool':'finish','arguments':{}}])
        report = run_agent(self.registry, self.request, lambda *_: next(actions))
        self.assertEqual(report['criteria'][0]['verdict'], 'supported')
        self.assertEqual(report['criteria'][1]['verdict'], 'unknown')
        self.assertEqual(len(report['agent_trace']), 2)

    def test_unknown_tool_and_fabricated_quote_never_produce_assertion(self):
        self.findings[0]['citations'][0]['quote'] = 'fabricated'
        for action in ({'tool':'shell','arguments':{'cmd':'anything'}},
                       {'tool':'submit','arguments':self.findings[0]}):
            report = run_agent(self.registry, self.request, lambda *_: action)
            self.assertEqual(report['criteria'][0]['verdict'], 'unknown')

    def test_infinite_planner_is_bounded(self):
        report = run_agent(self.registry, self.request,
                           lambda *_: {'tool':'retrieve','arguments':{'query':'Age'}}, max_steps=3)
        self.assertEqual(len(report['agent_trace']), 3)
        self.assertTrue(all(c['verdict']=='unknown' for c in report['criteria']))

    def test_timeout_fails_to_unknown(self):
        def planner(*args):
            raise TimeoutError('sensitive provider content')
        report = run_agent(self.registry, self.request, planner)
        self.assertNotIn('sensitive', json.dumps(report))
        self.assertEqual(report['criteria'][0]['verdict'], 'unknown')

    def test_correct_quote_cannot_support_wrong_verdict(self):
        self.findings[0]['verdict']='contradicted'
        report=run_agent(self.registry,self.request,lambda *_:{'tool':'submit','arguments':self.findings[0]})
        self.assertEqual(report['criteria'][0]['verdict'],'unknown')

    def test_context_budget_stops_before_planner(self):
        def planner(*args): raise AssertionError('must not call provider')
        report=run_agent(self.registry,self.request,planner,max_context_bytes=100)
        self.assertEqual(report['agent_trace'][0]['status'],'budget_exhausted')

    def test_check_dispatch_returns_source_bound_finding(self):
        def planner(instructions,observations):
            if not observations:return {'tool':'check','arguments':{'criterion_id':'age'}}
            if len(observations)==1:return {'tool':'submit','arguments':observations[0]['result']}
            return {'tool':'finish','arguments':{}}
        report=run_agent(self.registry,self.request,planner)
        self.assertEqual(report['criteria'][0]['verdict'],'supported')
