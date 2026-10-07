import unittest
from clinical_trial.comparison import compare


def row(patient, predicted='unknown', gold='unknown'):
    return {'patient_id':patient,'trial_id':'t','criterion_id':'c','kind':'exclusion',
            'gold':gold,'predicted':predicted,'evidence_correct':True,'latency_ms':1,'cost_usd':0}


class ComparisonTests(unittest.TestCase):
    def test_paired_delta_reports_coverage_tradeoff(self):
        result=compare([row('a','contradicted'),row('b','supported','supported')],
                       [row('b','supported','supported'),row('a')])
        self.assertEqual(result['delta']['accuracy'],.5)
        self.assertEqual(result['delta']['coverage'],-.5)
        self.assertEqual(result['delta']['false_no_barrier_per_criterion'],-.5)

    def test_bootstrap_reproducible_independent_of_order(self):
        a=[row('a'),row('b'),row('c')]
        b=[row('a','contradicted'),row('b'),row('c')]
        self.assertEqual(compare(a,b),compare(list(reversed(a)),list(reversed(b))))

    def test_single_patient_has_no_uncertainty_interval(self):
        self.assertIsNone(compare([row('a')],[row('a')])['patient_bootstrap_95pct'])

    def test_label_or_polarity_disagreement_rejected(self):
        for changed in [row('a',gold='supported'),{**row('a'),'kind':'inclusion'}]:
            with self.assertRaises(ValueError):compare([row('a')],[changed])

    def test_missing_cases_and_duplicate_ids_rejected(self):
        for candidate in [[row('b')],[row('a'),row('a')]]:
            with self.assertRaises(ValueError):compare([row('a')],candidate)

    def test_bad_bootstrap_configuration_rejected(self):
        with self.assertRaises(ValueError):compare([row('a')],[row('a')],repetitions=0)
