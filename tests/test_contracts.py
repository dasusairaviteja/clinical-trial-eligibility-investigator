"""Contract tests use authored strings, never clinical records."""

from dataclasses import FrozenInstanceError, replace
import unittest

from clinical_trial.contracts import (
    Citation, Criterion, CriterionKind, Finding, ReviewSignal,
    SourceDocument, Verdict, validate_finding,
)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.source = SourceDocument("record-1", "SYN-001", "v1", "Age: 54 years.")
        self.citation = Citation("record-1", "v1", 0, 7, "Age: 54")
        self.criterion = Criterion("age", "DEMO-1", CriterionKind.INCLUSION, "Age over 18")
        self.finding = Finding("age", Verdict.SUPPORTED, (self.citation,))

    def validate(self, finding=None, sources=None, criterion=None):
        return validate_finding(
            criterion or self.criterion, finding or self.finding, "SYN-001",
            (self.source,) if sources is None else sources,
        )

    def test_all_six_polarity_mappings(self):
        expected = {
            (CriterionKind.INCLUSION, Verdict.SUPPORTED): ReviewSignal.NO_BARRIER_ON_THIS_CRITERION,
            (CriterionKind.INCLUSION, Verdict.CONTRADICTED): ReviewSignal.POTENTIAL_BARRIER,
            (CriterionKind.EXCLUSION, Verdict.SUPPORTED): ReviewSignal.POTENTIAL_BARRIER,
            (CriterionKind.EXCLUSION, Verdict.CONTRADICTED): ReviewSignal.NO_BARRIER_ON_THIS_CRITERION,
            (CriterionKind.INCLUSION, Verdict.UNKNOWN): ReviewSignal.NEEDS_CLARIFICATION,
            (CriterionKind.EXCLUSION, Verdict.UNKNOWN): ReviewSignal.NEEDS_CLARIFICATION,
        }
        for (kind, verdict), signal in expected.items():
            with self.subTest(kind=kind, verdict=verdict):
                finding = Finding("age", verdict, (self.citation,),
                                  ("Confirm age",) if verdict == Verdict.UNKNOWN else ())
                self.assertEqual(self.validate(finding, criterion=replace(self.criterion, kind=kind)), signal)

    def test_definitive_verdict_requires_citation(self):
        for verdict in (Verdict.SUPPORTED, Verdict.CONTRADICTED):
            with self.subTest(verdict=verdict), self.assertRaises(ValueError):
                Finding("age", verdict)

    def test_unknown_requires_clarification(self):
        with self.assertRaises(ValueError):
            Finding("age", Verdict.UNKNOWN)
        unknown = Finding("age", Verdict.UNKNOWN, missing_information=("Confirm age",))
        self.assertEqual(self.validate(unknown, sources=()), ReviewSignal.NEEDS_CLARIFICATION)

    def test_invalid_source_references(self):
        for citation in (
            replace(self.citation, source_id="missing"),
            replace(self.citation, source_version="v2"),
            replace(self.citation, quote="Age: 55"),
            replace(self.citation, end=999),
        ):
            with self.subTest(citation=citation), self.assertRaises(ValueError):
                self.validate(replace(self.finding, citations=(citation,)))

    def test_other_patient_and_duplicate_source_are_rejected(self):
        for sources in ((replace(self.source, patient_id="SYN-002"),),
                        (self.source, self.source)):
            with self.subTest(sources=sources), self.assertRaises(ValueError):
                self.validate(sources=sources)

    def test_wrong_criterion_is_rejected(self):
        with self.assertRaises(ValueError):
            self.validate(replace(self.finding, criterion_id="other"))

    def test_invalid_offsets(self):
        for start, end in ((-1, 2), (2, 2), (3, 2), (True, 2), (0, 1.5)):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                Citation("record-1", "v1", start, end, "x")

    def test_unicode_character_offsets(self):
        source = replace(self.source, text="é🙂Age")
        citation = replace(self.citation, start=2, end=5, quote="Age")
        self.validate(replace(self.finding, citations=(citation,)), sources=(source,))

    def test_enum_and_collection_types_are_not_coerced(self):
        for changes in ({"verdict": "supported"}, {"citations": []},
                        {"missing_information": []}, {"citations": ("bad",)}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(self.finding, **changes)
        with self.assertRaises(ValueError):
            replace(self.criterion, kind="inclusion")

    def test_unresolved_information_cannot_be_definitive(self):
        with self.assertRaises(ValueError):
            replace(self.finding, missing_information=("Need more evidence",))

    def test_empty_fields_are_rejected(self):
        for value in ("", " ", None, 123):
            with self.subTest(value=value), self.assertRaises(ValueError):
                replace(self.source, text=value)

    def test_objects_are_immutable_and_repr_omits_record_text(self):
        with self.assertRaises(FrozenInstanceError):
            self.source.text = "changed"
        self.assertNotIn("Age: 54", repr(self.source))
        self.assertNotIn("Age: 54", repr(self.citation))


if __name__ == "__main__":
    unittest.main()
