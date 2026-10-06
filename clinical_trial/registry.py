"""Trusted, version-pinned patient evidence and trial criterion lookup."""

from dataclasses import dataclass
import json

from .contracts import Criterion, CriterionKind, SourceDocument, require_text
from .report import (
    CaseValidationError, MAX_INPUT_BYTES, _array, _build_report, _object,
    _reject_constant, _unique_object,
)

MAX_REGISTRY_BYTES = 10_000_000


@dataclass(frozen=True)
class SourceReference:
    source_id: str
    source_version: str


@dataclass(frozen=True)
class TrialReference:
    trial_id: str
    trial_version: str


@dataclass(frozen=True)
class TrialSnapshot:
    trial_id: str
    version: str
    criteria: tuple[Criterion, ...]

    def __post_init__(self):
        require_text(self.trial_id, "trial_id")
        require_text(self.version, "trial version")
        if not self.criteria or not all(
            isinstance(criterion, Criterion) for criterion in self.criteria
        ):
            raise ValueError("trial criteria must be a nonempty Criterion tuple")
        if any(criterion.trial_id != self.trial_id for criterion in self.criteria):
            raise ValueError("criterion belongs to another trial")
        if len({criterion.criterion_id for criterion in self.criteria}) != len(self.criteria):
            raise ValueError("criterion identifiers must be unique within a trial")


class TrustedRegistry:
    """Immutable data authority separated from caller-provided findings."""

    def __init__(self, sources: tuple[SourceDocument, ...],
                 trials: tuple[TrialSnapshot, ...]):
        if not isinstance(sources, tuple) or not all(
            isinstance(source, SourceDocument) for source in sources
        ):
            raise ValueError("sources must be validated SourceDocument objects")
        by_key = {(s.patient_id, s.source_id, s.version): s for s in sources}
        if len(by_key) != len(sources):
            raise ValueError("duplicate source snapshot")
        if not isinstance(trials, tuple) or not all(
            isinstance(trial, TrialSnapshot) for trial in trials
        ):
            raise ValueError("trials must be validated TrialSnapshot objects")
        by_trial = {(trial.trial_id, trial.version): trial for trial in trials}
        if len(by_trial) != len(trials):
            raise ValueError("duplicate trial snapshot")
        self._sources = by_key
        self._trials = by_trial

    def resolve_sources(self, patient_id: str,
                        references: tuple[SourceReference, ...]) -> tuple[SourceDocument, ...]:
        if not references or len(set(references)) != len(references):
            raise ValueError("source references must be nonempty and unique")
        resolved = []
        for reference in references:
            source = self._sources.get(
                (patient_id, reference.source_id, reference.source_version))
            if source is None:
                raise ValueError("source snapshot is unavailable")
            resolved.append(source)
        return tuple(resolved)

    def resolve_trial(self, reference: TrialReference) -> TrialSnapshot:
        trial = self._trials.get((reference.trial_id, reference.trial_version))
        if trial is None:
            raise ValueError("trial snapshot is unavailable")
        return trial


def registry_from_json(payload: bytes) -> TrustedRegistry:
    """Load a bounded registry file controlled by the service operator."""
    if type(payload) is not bytes or len(payload) > MAX_REGISTRY_BYTES:
        raise CaseValidationError("Invalid trusted source registry")
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object,
                           parse_constant=_reject_constant)
        _object(value, ("schema_version", "sources", "trials"))
        if type(value["schema_version"]) is not int or value["schema_version"] != 1:
            raise ValueError("unsupported registry version")
        sources = tuple(SourceDocument(**_object(item, (
            "source_id", "patient_id", "version", "text"
        ))) for item in _array(value["sources"]))
        trials = []
        for item in _array(value["trials"]):
            _object(item, ("trial_id", "version", "criteria"))
            criteria = tuple(Criterion(
                **{**_object(criterion, (
                    "criterion_id", "trial_id", "kind", "statement"
                )), "kind": CriterionKind(criterion["kind"])}
            ) for criterion in _array(item["criteria"]))
            trials.append(TrialSnapshot(item["trial_id"], item["version"], criteria))
        return TrustedRegistry(sources, tuple(trials))
    except (ValueError, TypeError, KeyError, RecursionError):
        raise CaseValidationError("Invalid trusted source registry") from None


def report_from_registry_json(payload: bytes, registry: TrustedRegistry) -> dict:
    """Build a report using only exact evidence and trial snapshots in the registry."""
    if type(payload) is not bytes or len(payload) > MAX_INPUT_BYTES:
        raise CaseValidationError("Invalid case request")
    if not isinstance(registry, TrustedRegistry):
        raise CaseValidationError("Trusted registry is unavailable")
    try:
        request = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object,
                             parse_constant=_reject_constant)
        _object(request, ("schema_version", "case_id", "patient_id", "trial_ref",
                          "source_refs", "findings"))
        references = tuple(SourceReference(**_object(item, (
            "source_id", "source_version"
        ))) for item in _array(request["source_refs"]))
        trial_reference = TrialReference(**_object(request["trial_ref"], (
            "trial_id", "trial_version"
        )))
        sources = registry.resolve_sources(request["patient_id"], references)
        trial = registry.resolve_trial(trial_reference)
        case = {key: value for key, value in request.items()
                if key not in ("source_refs", "trial_ref")}
        case["trial_id"] = trial.trial_id
        case["sources"] = [{
            "source_id": source.source_id,
            "patient_id": source.patient_id,
            "version": source.version,
            "text": source.text,
        } for source in sources]
        case["criteria"] = [{
            "criterion_id": criterion.criterion_id,
            "trial_id": criterion.trial_id,
            "kind": criterion.kind.value,
            "statement": criterion.statement,
        } for criterion in trial.criteria]
        return _build_report(case)
    except (ValueError, TypeError, KeyError, RecursionError):
        raise CaseValidationError("Invalid case request or unavailable evidence") from None
