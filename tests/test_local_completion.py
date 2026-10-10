"""Non-clinical fixtures covering the complete local research handoff."""
import copy
from email.message import Message
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from clinical_trial.adjudication import review_packet, score_review
from clinical_trial.agent import run_agent
from clinical_trial.cohort import run_cohort
from clinical_trial.contracts import Criterion, CriterionKind, SourceDocument
from clinical_trial.evidence_tools import check
from clinical_trial.registry import registry_from_json
from clinical_trial.tools import temporal_days
from clinical_trial.trial_fetch import fetch_snapshot, save_snapshot, NoRedirects

ROOT = Path(__file__).resolve().parents[1]


class TrialFetchTests(unittest.TestCase):
    def record(self):
        return {'protocolSection': {'identificationModule': {'nctId': 'NCT00000001'},
            'statusModule': {'lastUpdatePostDateStruct': {'date': '2026-10-01'}},
            'eligibilityModule': {'eligibilityCriteria': 'Inclusion Criteria:\n- Age over 18 years'}}}

    def client(self, raw, content_type='application/json'):
        response = io.BytesIO(raw)
        response.status = 200
        response.headers = Message()
        response.headers['Content-Type'] = content_type
        client = Mock()
        client.open.return_value = response
        return client

    def test_traceable_private_snapshot_and_no_overwrite(self):
        raw = json.dumps(self.record()).encode()
        client = self.client(raw)
        snapshot, body = fetch_snapshot('NCT00000001', opener=client)
        self.assertEqual(body, raw)
        self.assertEqual(snapshot['status'], 'human_review_required')
        self.assertFalse(snapshot['candidate']['automatic_promotion_allowed'])
        self.assertEqual(client.open.call_args.kwargs['timeout'], 20)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'snapshot'
            save_snapshot(snapshot, raw, target)
            self.assertEqual((target / 'record.json').read_bytes(), raw)
            self.assertEqual((target / 'record.json').stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                save_snapshot(snapshot, raw, target)

    def test_rejects_wrong_trial_duplicate_json_html_and_oversize(self):
        raw = json.dumps(self.record()).encode()
        cases = [(raw.replace(b'NCT00000001', b'NCT00000002'), 'application/json'),
                 (b'{"a":1,"a":2}', 'application/json'), (raw, 'text/html'),
                 (b' ' * 1_000_001, 'application/json')]
        for body, kind in cases:
            with self.subTest(kind=kind, length=len(body)), self.assertRaises(ValueError):
                fetch_snapshot('NCT00000001', opener=self.client(body, kind))

    def test_no_arbitrary_urls_or_redirects(self):
        client = Mock()
        with self.assertRaises(ValueError):
            fetch_snapshot('https://example.com/', opener=client)
        client.open.assert_not_called()
        with self.assertRaises(ValueError):
            NoRedirects().redirect_request(None, None, 302, '', {}, 'https://example.com/')


class DayWindowTests(unittest.TestCase):
    def test_boolean_measurement_cannot_become_numeric_evidence(self):
        source = SourceDocument('s', 'p', 'v1', json.dumps({'schema': 'synthetic-observation-v1',
            'patient_id': 'p', 'type': 'measurement', 'name': 'age', 'date': '2026-10-08',
            'value': True, 'unit': 'years'}))
        criterion = Criterion('c', 't', CriterionKind.INCLUSION, 'Age at least 1 years on 2026-10-08')
        self.assertEqual(check(criterion, [source])['verdict'], 'unknown')
    def test_compound_truth_tables_use_real_evidence_and_preserve_unknown(self):
        source = SourceDocument('s', 'p', 'v1', 'Age: 20 years.')
        clauses = {'supported': 'Age over 18 years', 'contradicted': 'Age under 18 years',
                   'unknown': 'Unsupported clinical phrase'}
        for operator in ['All', 'Any']:
            for left in clauses:
                for right in clauses:
                    criterion = Criterion('c', 't', CriterionKind.INCLUSION,
                        operator + ' of: ' + json.dumps([clauses[left], clauses[right]]))
                    result = check(criterion, [source])
                    decisive = 'contradicted' if operator == 'All' else 'supported'
                    expected = decisive if decisive in (left, right) else (
                        'unknown' if 'unknown' in (left, right) else left)
                    self.assertEqual(result['verdict'], expected)
                    if expected != 'unknown':
                        self.assertEqual(len(result['citations']), 1)
                        self.assertEqual(result['citations'][0]['quote'], source.text)

    def test_compound_rejects_nested_and_excessive_rules(self):
        for statements in [['Age over 18 years'], ['Age over 18 years'] * 9,
                           ['All of: []', 'Age over 18 years'], [None, 'Age over 18 years']]:
            criterion = Criterion('c', 't', CriterionKind.INCLUSION, 'All of: ' + json.dumps(statements))
            self.assertEqual(check(criterion, [])['verdict'], 'unknown')

    def test_leap_day_boundaries_and_missing_coverage(self):
        self.assertEqual(temporal_days(['2024-02-29'], '2024-03-01', 1), 'supported')
        self.assertEqual(temporal_days(['2024-02-28'], '2024-03-01', 1), 'unknown')
        self.assertEqual(temporal_days([], '2024-03-01', 1, '2024-02-29', '2024-03-01'), 'contradicted')
        for days in [True, -1, 36601]:
            self.assertEqual(temporal_days([], '2024-03-01', days), 'unknown')

    def test_source_bound_days_and_underflow_abstain(self):
        source = SourceDocument('s', 'p', 'v1', json.dumps({'schema': 'synthetic-observation-v1',
            'patient_id': 'p', 'type': 'event_history', 'name': 'stroke', 'events': ['2024-02-29']}))
        criterion = Criterion('c', 't', CriterionKind.EXCLUSION, 'Event stroke within 1 days before 2024-03-01')
        self.assertEqual(check(criterion, [source])['verdict'], 'supported')
        old = Criterion('c', 't', CriterionKind.EXCLUSION, 'Event stroke within 365 days before 0001-01-01')
        self.assertEqual(check(old, [source])['verdict'], 'unknown')


class CohortTests(unittest.TestCase):
    def test_nonfinite_or_boolean_deadline_rejected_before_planning(self):
        planner = Mock()
        for deadline in [float('nan'), float('inf'), True, '120']:
            with self.assertRaises(ValueError):
                run_agent(self.registry, self.request, planner, deadline_seconds=deadline)
        planner.assert_not_called()
    def setUp(self):
        self.registry = registry_from_json((ROOT / 'examples/synthetic_sources.json').read_bytes())
        self.request = json.loads((ROOT / 'examples/synthetic_request.json').read_bytes())
        for field in ['schema_version', 'findings']:
            self.request.pop(field)

    def cohort(self):
        return run_cohort(self.registry, [self.request])

    def test_rules_batch_preserves_totals_and_no_gold_leakage(self):
        cohort = self.cohort()
        rows = cohort['predictions']['rules']
        self.assertAlmostEqual(sum(r['latency_ms'] for r in rows), cohort['runs']['rules'][0]['latency_ms'])
        self.assertTrue(all('gold' not in row and row['cost_usd'] == 0 for row in rows))

    def test_all_references_preflight_before_planner_calls(self):
        factory = Mock()
        bad = {**self.request, 'trial_ref': {'trial_id': 'missing', 'trial_version': 'v1'}}
        with self.assertRaises(ValueError):
            run_cohort(self.registry, [self.request, bad], ['bounded_agent'],
                       planner_factory=factory, planner_provenance='scripted_test')
        factory.assert_not_called()

    def test_duplicate_cases_and_missing_planner_rejected(self):
        with self.assertRaises(ValueError):
            run_cohort(self.registry, [self.request, self.request])
        with self.assertRaises(ValueError):
            run_cohort(self.registry, [self.request], ['bounded_agent'])

    def test_scripted_agent_batch_keeps_unmeasured_cost_unknown(self):
        def factory(arm):
            def planner(instructions, observations):
                if not observations:
                    return {'tool': 'check', 'arguments': {'criterion_id': 'age'}}
                if len(observations) == 1:
                    return {'tool': 'submit', 'arguments': observations[0]['result']}
                return {'tool': 'finish', 'arguments': {}}
            return planner
        cohort = run_cohort(self.registry, [self.request], ['rules', 'bounded_agent'],
            planner_factory=factory, planner_provenance='scripted_software_test_not_llm')
        packet, key = review_packet(cohort)
        self.assertEqual(len(packet['gold_rows']), 2)
        self.assertEqual(len(packet['evidence_rows']), 4)
        self.assertNotIn('predicted', json.dumps(packet['gold_rows']))
        self.assertNotIn('verdict', json.dumps(packet['gold_rows']))
        result = score_review(cohort, key, self.completed(packet))
        self.assertIsNone(result['bounded_agent']['total_cost_usd'])
        self.assertEqual(result['bounded_agent']['unpriced_predictions'], 2)

    def completed(self, packet):
        completed = copy.deepcopy(packet)
        gold = {}
        for arm_runs in self.cohort()['runs'].values():
            for run in arm_runs:
                for criterion in run['report']['criteria']:
                    gold[(run['report']['patient_id'], run['report']['trial_id'],
                          criterion['criterion_id'])] = criterion['verdict']
        for row in completed['gold_rows']:
            identity = (row['patient_id'], row['trial_id'], row['criterion']['criterion_id'])
            row.update(gold=gold[identity], reviewer='fixture-only',
                       rationale='Authored software test, not clinical review')
        for row in completed['evidence_rows']:
            row.update(evidence_correct=True, reviewer='fixture-only',
                       rationale='Authored software test, not clinical review')
        return completed

    def test_review_packet_detached_and_complete_scoring(self):
        cohort = self.cohort()
        packet, key = review_packet(cohort)
        self.assertNotIn('arm', json.dumps(packet))
        self.assertNotIn('verdict', json.dumps(packet['gold_rows']))
        self.assertEqual(len(packet['gold_rows']), len(cohort['predictions']['rules']))
        result = score_review(cohort, key, self.completed(packet))
        self.assertIn('rules', result)
        packet['gold_rows'][0]['criterion']['statement'] = 'tampered'
        with self.assertRaises(ValueError):
            score_review(cohort, key, self.completed(packet))

    def test_incomplete_duplicate_and_changed_cohort_rejected(self):
        cohort = self.cohort()
        packet, key = review_packet(cohort)
        duplicate = copy.deepcopy(packet)
        duplicate['gold_rows'] *= 2
        for completed in [packet, {'schema_version': 2, 'gold_rows': [], 'evidence_rows': []}, duplicate]:
            with self.assertRaises(ValueError):
                score_review(cohort, key, completed)
        changed = copy.deepcopy(cohort)
        changed['planner_provenance'] = 'tampered'
        with self.assertRaises(ValueError):
            score_review(changed, key, self.completed(packet))

    def test_reviewers_are_named_in_both_separated_tasks(self):
        cohort = self.cohort()
        packet, key = review_packet(cohort)
        completed = self.completed(packet)
        completed['gold_rows'][0]['reviewer'] = ''
        with self.assertRaises(ValueError):
            score_review(cohort, key, completed)
        completed = self.completed(packet)
        completed['evidence_rows'][0]['reviewer'] = ''
        with self.assertRaises(ValueError):
            score_review(cohort, key, completed)
