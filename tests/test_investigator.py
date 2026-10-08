import json
from pathlib import Path
import unittest
from clinical_trial.investigator import investigate
from clinical_trial.registry import registry_from_json

ROOT = Path(__file__).resolve().parents[1]


class InvestigatorTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "examples/synthetic_sources.json").read_text())
        self.request = json.loads((ROOT / "examples/synthetic_request.json").read_text())
        self.request.pop("schema_version")
        self.request.pop("findings")

    def test_investigation_uses_verified_spans_and_abstains(self):
        registry = registry_from_json(json.dumps(self.data).encode())
        report = investigate(registry, self.request)
        self.assertEqual([c["verdict"] for c in report["criteria"]], ["supported", "unknown"])
        self.assertEqual(report["execution"]["tool_calls"], 2)
        self.assertEqual(report["status"], "human_review_required")

    def test_budget_exhaustion_returns_unknown_without_calls(self):
        registry = registry_from_json(json.dumps(self.data).encode())
        report = investigate(registry, self.request, max_tool_calls=0)
        self.assertTrue(all(c["verdict"] == "unknown" for c in report["criteria"]))
        self.assertEqual(report["execution"]["tool_calls"], 0)

    def test_conflicting_age_evidence_is_unknown(self):
        self.data["sources"][0]["text"] = "Age: 54 years. Age: 20 years."
        registry = registry_from_json(json.dumps(self.data).encode())
        self.assertEqual(investigate(registry, self.request)["criteria"][0]["verdict"], "unknown")

    def test_structured_temporal_rule_runs_offline(self):
        self.data['trials'][0]['criteria'][0]['statement'] = 'Event stroke within 6 months before 2026-10-06'
        source = self.data['sources'][0]
        source['text'] = json.dumps({'schema': 'synthetic-observation-v1',
            'patient_id': source['patient_id'], 'type': 'event_history', 'name': 'stroke',
            'events': [], 'complete_since': '2026-04-06', 'complete_through': '2026-10-06'})
        registry = registry_from_json(json.dumps(self.data).encode())
        report = investigate(registry, self.request, max_tool_calls=1)
        self.assertEqual(report['criteria'][0]['verdict'], 'contradicted')
        self.assertEqual(report['criteria'][1]['verdict'], 'unknown')
        self.assertEqual(report['execution']['tool_calls'], 1)
        self.assertEqual(report['execution']['model_calls'], 0)

    def test_invalid_budget_is_rejected(self):
        registry = registry_from_json(json.dumps(self.data).encode())
        for budget in [-1, True, 1.5, 501]:
            with self.assertRaises(ValueError):
                investigate(registry, self.request, max_tool_calls=budget)
