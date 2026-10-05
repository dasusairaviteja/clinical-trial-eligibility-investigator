"""Trusted, version-pinned evidence lookup for synthetic patient records."""

from dataclasses import dataclass
import json

from .contracts import SourceDocument
from .report import (
    CaseValidationError, MAX_INPUT_BYTES, _array, _build_report, _object,
    _reject_constant, _unique_object,
)

MAX_REGISTRY_BYTES = 10_000_000


@dataclass(frozen=True)
class SourceReference:
    source_id: str
    source_version: str


class TrustedSourceRegistry:
    """Immutable lookup whose record text is never supplied by an API request."""

    def __init__(self, sources: tuple[SourceDocument, ...]):
        if not isinstance(sources, tuple) or not all(
            isinstance(source, SourceDocument) for source in sources
        ):
            raise ValueError("sources must be validated SourceDocument objects")
        by_key = {(s.patient_id, s.source_id, s.version): s for s in sources}
        if len(by_key) != len(sources):
            raise ValueError("duplicate source snapshot")
        self._by_key = by_key

    def resolve(self, patient_id: str,
                references: tuple[SourceReference, ...]) -> tuple[SourceDocument, ...]:
        if not references or len(set(references)) != len(references):
            raise ValueError("source references must be nonempty and unique")
        resolved = []
        for reference in references:
            source = self._by_key.get(
                (patient_id, reference.source_id, reference.source_version))
            if source is None:
                raise ValueError("source snapshot is unavailable")
            resolved.append(source)
        return tuple(resolved)


def registry_from_json(payload: bytes) -> TrustedSourceRegistry:
    """Load a bounded registry file controlled by the service operator."""
    if type(payload) is not bytes or len(payload) > MAX_REGISTRY_BYTES:
        raise CaseValidationError("Invalid trusted source registry")
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object,
                           parse_constant=_reject_constant)
        _object(value, ("schema_version", "sources"))
        if type(value["schema_version"]) is not int or value["schema_version"] != 1:
            raise ValueError("unsupported registry version")
        sources = tuple(SourceDocument(**_object(item, (
            "source_id", "patient_id", "version", "text"
        ))) for item in _array(value["sources"]))
        return TrustedSourceRegistry(sources)
    except (ValueError, TypeError, KeyError, RecursionError):
        raise CaseValidationError("Invalid trusted source registry") from None


def report_from_registry_json(payload: bytes, registry: TrustedSourceRegistry) -> dict:
    """Build a report using only exact source snapshots held by ``registry``."""
    if type(payload) is not bytes or len(payload) > MAX_INPUT_BYTES:
        raise CaseValidationError("Invalid case request")
    if not isinstance(registry, TrustedSourceRegistry):
        raise CaseValidationError("Trusted source registry is unavailable")
    try:
        request = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object,
                             parse_constant=_reject_constant)
        _object(request, ("schema_version", "case_id", "patient_id", "trial_id",
                          "source_refs", "criteria", "findings"))
        references = tuple(SourceReference(**_object(item, (
            "source_id", "source_version"
        ))) for item in _array(request["source_refs"]))
        sources = registry.resolve(request["patient_id"], references)
        case = {key: value for key, value in request.items() if key != "source_refs"}
        case["sources"] = [{
            "source_id": source.source_id,
            "patient_id": source.patient_id,
            "version": source.version,
            "text": source.text,
        } for source in sources]
        return _build_report(case)
    except (ValueError, TypeError, KeyError, RecursionError):
        raise CaseValidationError("Invalid case request or unavailable evidence") from None
