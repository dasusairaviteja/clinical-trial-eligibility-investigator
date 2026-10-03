"""Strict JSON case validation and deterministic review report generation."""

import argparse
import json
from pathlib import Path
import sys

from .contracts import (
    Citation, Criterion, CriterionKind, Finding, SourceDocument, Verdict,
    require_text, validate_finding,
)

MAX_INPUT_BYTES = 1_000_000
MAX_ITEMS = 500


class CaseValidationError(ValueError):
    """Safe boundary error that does not echo supplied record contents."""


def _object(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError("object fields do not match the schema")
    return value


def _array(value):
    if type(value) is not list or len(value) > MAX_ITEMS:
        raise ValueError("expected a bounded array")
    return value


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("nonstandard JSON number")


def _build_report(case):
    _object(case, ("schema_version", "case_id", "patient_id", "trial_id",
                   "sources", "criteria", "findings"))
    if type(case["schema_version"]) is not int or case["schema_version"] != 1:
        raise ValueError("unsupported schema version")
    for name in ("case_id", "patient_id", "trial_id"):
        require_text(case[name], name)

    sources = tuple(SourceDocument(**_object(item, (
        "source_id", "patient_id", "version", "text"
    ))) for item in _array(case["sources"]))

    criteria = []
    for item in _array(case["criteria"]):
        _object(item, ("criterion_id", "trial_id", "kind", "statement"))
        criterion = Criterion(**{**item, "kind": CriterionKind(item["kind"])})
        if criterion.trial_id != case["trial_id"]:
            raise ValueError("criterion belongs to another trial")
        criteria.append(criterion)
    if not criteria or len({c.criterion_id for c in criteria}) != len(criteria):
        raise ValueError("criteria must be nonempty and unique")

    findings = {}
    for item in _array(case["findings"]):
        _object(item, ("criterion_id", "verdict", "citations", "missing_information"))
        citations = tuple(Citation(**_object(citation, (
            "source_id", "source_version", "start", "end", "quote"
        ))) for citation in _array(item["citations"]))
        finding = Finding(item["criterion_id"], Verdict(item["verdict"]), citations,
                          tuple(_array(item["missing_information"])))
        if finding.criterion_id in findings:
            raise ValueError("duplicate finding")
        findings[finding.criterion_id] = finding
    if set(findings) != {c.criterion_id for c in criteria}:
        raise ValueError("exactly one finding is required per criterion")

    rows = []
    for criterion in criteria:
        finding = findings[criterion.criterion_id]
        signal = validate_finding(criterion, finding, case["patient_id"], sources)
        rows.append({
            "criterion_id": criterion.criterion_id,
            "kind": criterion.kind.value,
            "statement": criterion.statement,
            "verdict": finding.verdict.value,
            "review_signal": signal.value,
            "citations": [{"source_id": c.source_id, "source_version": c.source_version,
                           "start": c.start, "end": c.end, "quote": c.quote}
                          for c in finding.citations],
            "missing_information": list(finding.missing_information),
        })
    return {
        "schema_version": 1,
        "case_id": case["case_id"],
        "patient_id": case["patient_id"],
        "trial_id": case["trial_id"],
        "status": "human_review_required",
        "validation_scope": "structure_and_citation_provenance_only",
        "criteria": rows,
    }


def report_from_json(payload: bytes) -> dict:
    """Validate a bounded UTF-8 case atomically; return no partial report.

    Caller provides trusted case/source context. This is not authentication,
    clinical entailment verification, or compatibility with UI demo exports.
    """
    if type(payload) is not bytes or len(payload) > MAX_INPUT_BYTES:
        raise CaseValidationError("Case must be UTF-8 JSON within the size limit")
    try:
        case = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object,
                          parse_constant=_reject_constant)
        return _build_report(case)
    except (ValueError, TypeError, KeyError, RecursionError):
        raise CaseValidationError("Invalid case JSON, schema, or evidence references") from None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path, help="Synthetic case JSON file")
    args = parser.parse_args()
    try:
        with args.case.open("rb") as stream:
            report = report_from_json(stream.read(MAX_INPUT_BYTES + 1))
    except (OSError, CaseValidationError):
        print("Case rejected: unreadable input or invalid case/evidence.", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
