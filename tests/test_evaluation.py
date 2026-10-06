import unittest
from clinical_trial.evaluation import evaluate, validate_disjoint, bootstrap_accuracy


def row(patient, kind, gold, predicted):
    return dict(patient_id=patient, trial_id='trial-'+patient, criterion_id='c1',
                kind=kind, gold=gold, predicted=predicted, evidence_correct=False,
                latency_ms=1, cost_usd=0)


class EvaluationTests(unittest.TestCase):
    def test_exclusion_polarity_and_abstention_do_not_hide_errors(self):
        rows = [row('a','exclusion','supported','contradicted'),
                row('b','inclusion','unknown','supported'),
                row('c','inclusion','supported','unknown')]
        metrics = evaluate(rows)
        self.assertEqual(metrics['false_no_barrier_count'], 2)
        self.assertEqual(metrics['coverage'], 2/3)
        self.assertEqual(metrics['false_no_barrier_rate'], 1)

    def test_all_unknown_has_zero_coverage_and_no_assertion_rate(self):
        metrics = evaluate([row('a','inclusion','unknown','unknown')])
        self.assertEqual(metrics['coverage'], 0)
        self.assertIsNone(metrics['false_no_barrier_rate'])

    def test_disjoint_rejects_patient_and_trial_leakage(self):
        a = row('a','inclusion','unknown','unknown')
        b = row('b','inclusion','unknown','unknown')
        validate_disjoint({'train':[a], 'test':[b]})
        with self.assertRaises(ValueError):
            validate_disjoint({'train':[a], 'test':[a]})
        b['trial_id'] = a['trial_id']
        with self.assertRaises(ValueError):
            validate_disjoint({'train':[a], 'test':[b]})

    def test_duplicates_and_nonfinite_cost_rejected(self):
        a = row('a','inclusion','unknown','unknown')
        with self.assertRaises(ValueError):
            evaluate([a,a])
        a['cost_usd'] = float('nan')
        with self.assertRaises(ValueError):
            evaluate([a])

    def test_bootstrap_is_reproducible(self):
        rows = [row('a','inclusion','supported','supported'), row('b','inclusion','supported','unknown')]
        self.assertEqual(bootstrap_accuracy(rows), bootstrap_accuracy(rows))
