import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from clinical_trial.report import CaseValidationError, MAX_INPUT_BYTES, report_from_json

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "synthetic_case.json"


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.case = json.loads(EXAMPLE.read_text())

    def report(self, case=None):
        return report_from_json(json.dumps(self.case if case is None else case).encode())

    def test_report_is_deterministic_and_requires_review(self):
        result = self.report()
        self.assertEqual(result, self.report())
        self.assertEqual(result["status"], "human_review_required")
        self.assertEqual(result["criteria"][1]["review_signal"], "needs_clarification")
        self.assertNotIn("sources", result)

    def test_unknown_fields_and_missing_fields(self):
        for case in ({**self.case, "eligible": True},
                     {k: v for k, v in self.case.items() if k != "trial_id"}):
            with self.subTest(case=case), self.assertRaises(CaseValidationError):
                self.report(case)

    def test_duplicate_keys_and_nonstandard_numbers(self):
        for payload in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.subTest(payload=payload), self.assertRaises(CaseValidationError):
                report_from_json(payload)

    def test_invalid_root_encoding_size_and_depth(self):
        for payload in (b'[]', b'null', b'\xff', b'{', b' ' * (MAX_INPUT_BYTES + 1),
                        b'[' * 2000 + b']' * 2000):
            with self.subTest(length=len(payload)), self.assertRaises(CaseValidationError):
                report_from_json(payload)

    def test_wrong_versions_are_not_coerced(self):
        for version in (True, 1.0, "1", 2):
            with self.subTest(version=version), self.assertRaises(CaseValidationError):
                self.report({**self.case, "schema_version": version})

    def test_arrays_and_item_limits(self):
        for field in ("criteria", "sources", "findings"):
            for value in ({}, None, [self.case[field][0]] * 501):
                with self.subTest(field=field), self.assertRaises(CaseValidationError):
                    self.report({**self.case, field: value})

    def test_criterion_and_finding_cardinality(self):
        mutations = [
            ("criteria", []), ("criteria", self.case["criteria"] * 2),
            ("findings", self.case["findings"][:1]),
            ("findings", self.case["findings"] * 2),
        ]
        for field, value in mutations:
            with self.subTest(field=field), self.assertRaises(CaseValidationError):
                self.report({**self.case, field: value})

    def test_cross_trial_and_cross_patient_rejected(self):
        for collection, field in (("criteria", "trial_id"), ("sources", "patient_id")):
            case = copy.deepcopy(self.case)
            case[collection][0][field] = "other"
            with self.subTest(collection=collection), self.assertRaises(CaseValidationError):
                self.report(case)

    def test_bad_quote_rejected_without_echo(self):
        self.case["findings"][0]["citations"][0]["quote"] = "PRIVATE_INPUT_MARKER"
        with self.assertRaises(CaseValidationError) as caught:
            self.report()
        self.assertNotIn("PRIVATE_INPUT_MARKER", str(caught.exception))

    def test_unknown_nested_field_and_bad_enum(self):
        case = copy.deepcopy(self.case)
        case["sources"][0]["extra"] = True
        with self.assertRaises(CaseValidationError):
            self.report(case)
        self.case["findings"][0]["verdict"] = "eligible"
        with self.assertRaises(CaseValidationError):
            self.report()

    def test_findings_are_emitted_in_criterion_order(self):
        self.case["findings"].reverse()
        self.assertEqual([r["criterion_id"] for r in self.report()["criteria"]],
                         ["age", "admission"])

    def test_cli_valid_case(self):
        result = subprocess.run([sys.executable, "-m", "clinical_trial.report", str(EXAMPLE)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "human_review_required")

    def test_cli_invalid_case_has_no_partial_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text('{"private":"PRIVATE_INPUT_MARKER"}')
            result = subprocess.run([sys.executable, "-m", "clinical_trial.report", str(path)],
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("PRIVATE_INPUT_MARKER", result.stderr)
