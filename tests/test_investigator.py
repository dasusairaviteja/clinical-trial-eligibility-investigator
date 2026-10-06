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
