import copy
import json
from pathlib import Path
import unittest

from clinical_trial.registry import registry_from_json, report_from_registry_json
from clinical_trial.report import CaseValidationError

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "examples" / "synthetic_sources.json"
REQUEST = ROOT / "examples" / "synthetic_request.json"


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = registry_from_json(REGISTRY.read_bytes())
        self.request = json.loads(REQUEST.read_text())

    def report(self, value=None):
        return report_from_registry_json(
            json.dumps(self.request if value is None else value).encode(), self.registry)

    def test_exact_reference_resolves_trusted_snapshot(self):
        report = self.report()
        self.assertEqual(report["criteria"][0]["citations"][0]["quote"], "Age: 54")
        self.assertNotIn("sources", report)

    def test_caller_cannot_supply_or_override_source_text(self):
        for extra in ({"sources": []}, {"text": "Age: 99"}, {"criteria": []},
                      {"trial_id": "CALLER-TRIAL"}):
            with self.subTest(extra=extra), self.assertRaises(CaseValidationError):
                self.report({**self.request, **extra})

    def test_unknown_patient_source_or_version_fails_closed(self):
        mutations = [("patient_id", "SYN-OTHER"),
                     ("source_id", "missing"), ("source_version", "v2")]
        for field, value in mutations:
            request = copy.deepcopy(self.request)
            if field == "patient_id":
                request[field] = value
            else:
                request["source_refs"][0][field] = value
            with self.subTest(field=field), self.assertRaises(CaseValidationError):
                self.report(request)

    def test_duplicate_references_and_snapshots_fail_closed(self):
        request = copy.deepcopy(self.request)
        request["source_refs"] *= 2
        with self.assertRaises(CaseValidationError):
            self.report(request)
        value = json.loads(REGISTRY.read_text())
        value["sources"] *= 2
        with self.assertRaises(CaseValidationError):
            registry_from_json(json.dumps(value).encode())

    def test_trial_snapshot_is_version_pinned_and_operator_controlled(self):
        report = self.report()
        self.assertEqual([item["criterion_id"] for item in report["criteria"]],
                         ["age", "admission"])
        self.assertEqual(report["trial_id"], "DEMO-TRIAL-001")
        for field, value in (("trial_id", "missing"),
                             ("trial_version", "stale-version")):
            request = copy.deepcopy(self.request)
            request["trial_ref"][field] = value
            with self.subTest(field=field), self.assertRaises(CaseValidationError):
                self.report(request)

    def test_duplicate_trial_and_criterion_snapshots_fail_closed(self):
        value = json.loads(REGISTRY.read_text())
        value["trials"] *= 2
        with self.assertRaises(CaseValidationError):
            registry_from_json(json.dumps(value).encode())
        value = json.loads(REGISTRY.read_text())
        value["trials"][0]["criteria"] *= 2
        with self.assertRaises(CaseValidationError):
            registry_from_json(json.dumps(value).encode())

    def test_registry_parser_is_strict_and_non_echoing(self):
        for payload in (b'{"schema_version":1,"sources":[],"trials":[],"private":"MARKER"}',
                        b'{"schema_version":1,"schema_version":1,"sources":[],"trials":[]}'):
            with self.subTest(payload=payload), self.assertRaises(CaseValidationError) as caught:
                registry_from_json(payload)
            self.assertNotIn("MARKER", str(caught.exception))
