import unittest
from clinical_trial.synthetic_study import run_study
from clinical_trial.evidence_tools import check
from clinical_trial.contracts import Criterion, CriterionKind


class AblationTests(unittest.TestCase):
    def test_controls_change_only_intended_fixture_predictions(self):
        study=run_study()
        rows={arm:{r['patient_id']:r['predicted'] for r in values} for arm,values in study['predictions'].items()}
        self.assertEqual(rows['bounded_agent']['SYN-old_event'],'contradicted')
        self.assertEqual(rows['without_temporal']['SYN-old_event'],'supported')
        self.assertEqual(rows['bounded_agent']['SYN-missing_history'],'unknown')
        self.assertEqual(rows['without_missing_evidence_control']['SYN-missing_history'],'contradicted')
        for arm in rows:
            self.assertEqual(rows[arm]['SYN-recent_event'],'supported')
            self.assertEqual(rows[arm]['SYN-complete_absence'],'contradicted')
        self.assertEqual(study['model_calls'],0)

    def test_unknown_ablation_rejected(self):
        criterion=Criterion('c','t',CriterionKind.EXCLUSION,'unsupported')
        with self.assertRaises(ValueError):check(criterion,[],research_ablation='anything')
