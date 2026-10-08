"""Bounded offline investigator; a rules baseline, not an LLM experiment."""

import json
import time

from .registry import SourceReference, TrialReference, report_from_registry_json
from .evidence_tools import check


def investigate(registry, request, max_tool_calls=50):
    if type(max_tool_calls) is not int or not 0 <= max_tool_calls <= 500:
        raise ValueError("max_tool_calls must be an integer from 0 to 500")
    if set(request) != {"case_id", "patient_id", "trial_ref", "source_refs"}:
        raise ValueError("invalid investigation request")
    trial = registry.resolve_trial(TrialReference(**request["trial_ref"]))
    sources = registry.resolve_sources(request["patient_id"], tuple(
        SourceReference(**reference) for reference in request["source_refs"]))
    start = time.perf_counter()
    findings, trace, calls = [], [], 0
    for criterion in trial.criteria:
        finding = {"criterion_id": criterion.criterion_id, "verdict": "unknown",
                   "citations": [], "missing_information": ["Requires qualified review of this criterion."]}
        if calls < max_tool_calls:
            finding = check(criterion, sources)
            calls += 1
            trace.append({"tool": "check", "criterion_id": criterion.criterion_id,
                          "verdict": finding["verdict"]})
        else:
            finding["missing_information"] = ["Investigation tool budget exhausted; manual review required."]
        findings.append(finding)
    payload = {"schema_version": 1, **request, "findings": findings}
    report = report_from_registry_json(json.dumps(payload).encode(), registry)
    report["trial_version"] = trial.version
    report["execution"] = {"engine": "rules-baseline-v2", "tool_calls": calls,
                           "max_tool_calls": max_tool_calls, "trace": trace,
                           "latency_ms": round((time.perf_counter()-start)*1000, 3),
                           "model_calls": 0, "model_cost_usd": 0}
    return report
