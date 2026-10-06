from datetime import date
import unittest

from clinical_trial.tools import calendar_months_before, numerical, temporal
from clinical_trial.ingestion import parse_criteria


class ScreeningToolsTests(unittest.TestCase):
    def test_calendar_window_clamps_month_end(self):
        self.assertEqual(calendar_months_before(date(2024, 3, 31), 1), date(2024, 2, 29))
        self.assertEqual(calendar_months_before(date(2025, 3, 31), 1), date(2025, 2, 28))

    def test_temporal_boundaries_and_future_events(self):
        self.assertEqual(temporal(["2024-02-29"], "2024-03-31", 1), "supported")
        self.assertEqual(temporal(["2024-04-01"], "2024-03-31", 1), "unknown")
        self.assertEqual(temporal(["2024-02-28"], "2024-03-31", 1), "unknown")

    def test_negative_requires_complete_window(self):
        self.assertEqual(temporal([], "2024-03-31", 1, "2024-03-01", "2024-03-31"), "unknown")
        self.assertEqual(temporal([], "2024-03-31", 1, "2024-02-01", "2024-03-31"), "contradicted")
        self.assertEqual(temporal(["invalid"], "2024-03-31", 1), "unknown")

    def test_numbers_preserve_boundary_and_units(self):
        self.assertEqual(numerical("18", "gt", "18", "years", "years"), "contradicted")
        self.assertEqual(numerical("18", "gte", "18", "years", "years"), "supported")
        for value in (None, "NaN", "Infinity", "invalid"):
            self.assertEqual(numerical(value, "gt", "18", "years", "years"), "unknown")
        self.assertEqual(numerical("20", "gt", "18", "months", "years"), "unknown")

    def test_parser_preserves_unicode_offsets_and_polarity(self):
        text = "Inclusion Criteria:\n- Age ≥ 18\nExclusion Criteria:\n- Prior admission\n"
        result = parse_criteria("NCT00000001", "2026-10-01", text)
        self.assertEqual([r["kind"] for r in result["criteria"]], ["inclusion", "exclusion"])
        for row in result["criteria"]:
            self.assertEqual(text[row["start"]:row["end"]], row["statement"])
        self.assertFalse(result["automatic_promotion_allowed"])

    def test_parser_marks_multiline_and_ambiguous_input(self):
        result = parse_criteria("NCT00000001", "2026-10-01", "Inclusion Criteria:\n- Age\n  continuation")
        self.assertEqual(len(result["issues"]), 1)
        with self.assertRaises(ValueError):
            parse_criteria("bad", "2026-10-01", "anything")
