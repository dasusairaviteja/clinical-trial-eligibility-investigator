"""Validated evidence contracts, not a clinical reasoning or enrollment engine."""

from dataclasses import dataclass, field
from enum import StrEnum


class CriterionKind(StrEnum):
    INCLUSION = "inclusion"
    EXCLUSION = "exclusion"


class Verdict(StrEnum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    UNKNOWN = "unknown"


class ReviewSignal(StrEnum):
    POTENTIAL_BARRIER = "potential_barrier"
    NEEDS_CLARIFICATION = "needs_clarification"
    NO_BARRIER_ON_THIS_CRITERION = "no_barrier_on_this_criterion"


def require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonempty text")


@dataclass(frozen=True)
class Criterion:
    criterion_id: str
    trial_id: str
    kind: CriterionKind
    statement: str = field(repr=False)

    def __post_init__(self) -> None:
        for name in ("criterion_id", "trial_id", "statement"):
            require_text(getattr(self, name), name)
        if not isinstance(self.kind, CriterionKind):
            raise ValueError("kind must be a CriterionKind")


@dataclass(frozen=True)
class SourceDocument:
    source_id: str
    patient_id: str
    version: str
    text: str = field(repr=False)

    def __post_init__(self) -> None:
        for name in ("source_id", "patient_id", "version", "text"):
            require_text(getattr(self, name), name)


@dataclass(frozen=True)
class Citation:
    source_id: str
    source_version: str
    start: int
    end: int
    quote: str = field(repr=False)

    def __post_init__(self) -> None:
        for name in ("source_id", "source_version", "quote"):
            require_text(getattr(self, name), name)
        # bool is an int subclass, but is never a valid character offset here.
        if type(self.start) is not int or type(self.end) is not int:
            raise ValueError("citation offsets must be integers")
        if not 0 <= self.start < self.end:
            raise ValueError("citation offsets must define a nonempty span")


@dataclass(frozen=True)
class Finding:
    criterion_id: str
    verdict: Verdict
    citations: tuple[Citation, ...] = ()
    missing_information: tuple[str, ...] = field(default=(), repr=False)

    def __post_init__(self) -> None:
        require_text(self.criterion_id, "criterion_id")
        if not isinstance(self.verdict, Verdict):
            raise ValueError("verdict must be a Verdict")
        if not isinstance(self.citations, tuple) or not all(
            isinstance(item, Citation) for item in self.citations
        ):
            raise ValueError("citations must be a tuple of Citation objects")
        if not isinstance(self.missing_information, tuple):
            raise ValueError("missing_information must be a tuple")
        for item in self.missing_information:
            require_text(item, "missing_information item")
        if self.verdict == Verdict.UNKNOWN:
            if not self.missing_information:
                raise ValueError("unknown findings require a clarification question")
        elif not self.citations:
            raise ValueError("supported or contradicted findings require evidence")
        elif self.missing_information:
            raise ValueError("unresolved information requires an unknown finding")


def validate_finding(
    criterion: Criterion,
    finding: Finding,
    patient_id: str,
    sources: tuple[SourceDocument, ...],
) -> ReviewSignal:
    """Check provenance and polarity; never establish overall eligibility.

    Offsets are Python Unicode character indices, end-exclusive, into the exact
    source snapshot. Matching a quote does NOT prove that it supports a verdict.
    Semantic entailment, record completeness, and temporal validity require
    separate evaluation and human review.
    """
    if not isinstance(criterion, Criterion) or not isinstance(finding, Finding):
        raise ValueError("criterion and finding must use validated contracts")
    require_text(patient_id, "patient_id")
    if not isinstance(sources, tuple) or not all(
        isinstance(source, SourceDocument) for source in sources
    ):
        raise ValueError("sources must be a tuple of SourceDocument objects")
    if finding.criterion_id != criterion.criterion_id:
        raise ValueError("finding does not match the criterion")
    by_id = {source.source_id: source for source in sources}
    if len(by_id) != len(sources):
        raise ValueError("duplicate source identifiers are ambiguous")
    if any(source.patient_id != patient_id for source in sources):
        raise ValueError("source collection contains another patient's evidence")
    for citation in finding.citations:
        source = by_id.get(citation.source_id)
        if source is None:
            raise ValueError("citation references an unavailable source")
        if source.version != citation.source_version:
            raise ValueError("citation references another source version")
        if citation.end > len(source.text):
            raise ValueError("citation extends beyond the source")
        if source.text[citation.start:citation.end] != citation.quote:
            raise ValueError("citation quote does not match the source span")
    if finding.verdict == Verdict.UNKNOWN:
        return ReviewSignal.NEEDS_CLARIFICATION
    barrier = (
        criterion.kind == CriterionKind.INCLUSION
        and finding.verdict == Verdict.CONTRADICTED
    ) or (
        criterion.kind == CriterionKind.EXCLUSION
        and finding.verdict == Verdict.SUPPORTED
    )
    return (
        ReviewSignal.POTENTIAL_BARRIER if barrier
        else ReviewSignal.NO_BARRIER_ON_THIS_CRITERION
    )
