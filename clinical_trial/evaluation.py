"""Evaluate aligned criterion predictions; never invent missing experiment outputs."""

import argparse
import hashlib
import json
from pathlib import Path
import random

LABELS = ("supported", "contradicted", "unknown")


def evaluate(rows):
    if not rows:
        raise ValueError("evaluation requires labeled predictions")
    identifiers = set()
    for row in rows:
        identity = (row["patient_id"], row["trial_id"], row["criterion_id"])
        if identity in identifiers:
            raise ValueError("duplicate prediction")
        identifiers.add(identity)
        if row["gold"] not in LABELS or row["predicted"] not in LABELS:
            raise ValueError("invalid label")
        if row["kind"] not in ("inclusion", "exclusion"):
            raise ValueError("invalid criterion kind")
        if type(row["evidence_correct"]) is not bool:
            raise ValueError("evidence accuracy requires explicit adjudication")
        for field in ("latency_ms", "cost_usd"):
            if field == 'cost_usd' and row[field] is None:
                continue  # Unknown billing must stay unknown, never become zero.
            if type(row[field]) not in (int, float) or not 0 <= row[field] < float('inf'):
                raise ValueError("invalid measured cost or latency")
    scores = []
    for label in LABELS:
        tp = sum(r["gold"] == label and r["predicted"] == label for r in rows)
        fp = sum(r["gold"] != label and r["predicted"] == label for r in rows)
        fn = sum(r["gold"] == label and r["predicted"] != label for r in rows)
        scores.append(2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0)
    assertions = [r for r in rows if (r["kind"], r["predicted"]) in
                  (("inclusion", "supported"), ("exclusion", "contradicted"))]
    definitive = [r for r in rows if r["predicted"] != "unknown"]
    false_assertions = sum(r["predicted"] != r["gold"] for r in assertions)
    return {"n": len(rows), "macro_f1": sum(scores)/len(scores),
            "coverage": len(definitive)/len(rows),
            "false_no_barrier_count": false_assertions,
            "no_barrier_assertion_count": len(assertions),
            "false_no_barrier_rate": false_assertions/len(assertions) if assertions else None,
            "evidence_accuracy": sum(r["evidence_correct"] for r in definitive)/len(definitive) if definitive else None,
            "mean_latency_ms": sum(r["latency_ms"] for r in rows)/len(rows),
            "total_cost_usd": None if any(r['cost_usd'] is None for r in rows) else sum(r["cost_usd"] for r in rows),
            "unpriced_predictions": sum(r['cost_usd'] is None for r in rows)}


def validate_disjoint(splits):
    seen_patients, seen_trials = set(), set()
    for name, rows in splits.items():
        patients = {r["patient_id"] for r in rows}
        trials = {r["trial_id"] for r in rows}
        if patients & seen_patients or trials & seen_trials:
            raise ValueError("patient or trial leakage between splits")
        seen_patients.update(patients)
        seen_trials.update(trials)


def bootstrap_accuracy(rows, seed=42, repetitions=1000):
    """Patient-cluster bootstrap; dependence between a patient's rows is retained."""
    groups = {}
    for row in rows:
        groups.setdefault(row["patient_id"], []).append(row)
    if len(groups) < 2:
        return None
    rng, values, patients = random.Random(seed), [], sorted(groups)
    for _ in range(repetitions):
        sample = [r for p in rng.choices(patients, k=len(patients)) for r in groups[p]]
        values.append(sum(r["gold"] == r["predicted"] for r in sample)/len(sample))
    values.sort()
    return [values[int(.025*repetitions)], values[min(int(.975*repetitions), repetitions-1)]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions", type=Path)
    args = parser.parse_args()
    raw = args.predictions.read_bytes()
    rows = json.loads(raw)
    result = evaluate(rows)
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    result["accuracy_95pct_patient_bootstrap"] = bootstrap_accuracy(rows)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
