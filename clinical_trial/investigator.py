"""Bounded offline investigator; a rules baseline, not an LLM experiment."""

import json
import re
import time

from .registry import SourceReference, TrialReference, report_from_registry_json
from .tools import numerical


def investigate(registry, request, max_tool_calls=50):
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
        # Deliberately narrow grammar: never infer arbitrary clinical meaning.
        age_rule = re.fullmatch(r"Age (over|at least|under|at most) ([0-9]+) years", criterion.statement)
        if age_rule and calls + 2 <= max_tool_calls:
            calls += 1
            matches = [(source, match) for source in sources for match in
                       re.finditer(r"\bAge: ([0-9]+) years\.", source.text)]
            trace.append({"tool": "retrieve_age", "criterion_id": criterion.criterion_id,
                          "matches": len(matches)})
            if len(matches) == 1:
                source, match = matches[0]
                calls += 1
                operator = {"over": "gt", "at least": "gte", "under": "lt", "at most": "lte"}[age_rule[1]]
                verdict = numerical(match[1], operator, age_rule[2], "years", "years")
                finding.update(verdict=verdict, missing_information=[], citations=[{
                    "source_id": source.source_id, "source_version": source.version,
                    "start": match.start(), "end": match.end(), "quote": match[0]}])
                trace.append({"tool": "numerical", "criterion_id": criterion.criterion_id,
                              "verdict": verdict})
            else:
                finding["missing_information"] = ["Provide one unambiguous dated age assessment."]
        elif calls + 2 > max_tool_calls:
            finding["missing_information"] = ["Investigation tool budget exhausted; manual review required."]
        findings.append(finding)
    payload = {"schema_version": 1, **request, "findings": findings}
    report = report_from_registry_json(json.dumps(payload).encode(), registry)
    report["trial_version"] = trial.version
    report["execution"] = {"engine": "rules-baseline-v1", "tool_calls": calls,
                           "max_tool_calls": max_tool_calls, "trace": trace,
                           "latency_ms": round((time.perf_counter()-start)*1000, 3),
                           "model_calls": 0, "model_cost_usd": 0}
    return report
