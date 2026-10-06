# Research release checklist

The supplied examples are fictional engineering fixtures, not clinical gold labels.
Passing tests is not evidence that the research hypothesis holds.

## Implemented

- Single bounded agent with retrieval, numerical, temporal and submission tools.
- Exact citation provenance checks and unknown-on-failure behavior.
- Reproducible local rules baseline for a deliberately narrow age-rule grammar.
- Evaluation CLI: `python -m clinical_trial.evaluation predictions.json`.
- Polarity-aware false no-barrier assertions, coverage, macro-F1, adjudicated
  evidence accuracy, latency, cost and patient-cluster bootstrap uncertainty.
- Patient/trial overlap validator and protocol in `experiments/protocol.json`.

Each prediction row contains patient_id, trial_id, criterion_id, kind, gold,
predicted, evidence_correct, latency_ms and cost_usd. Evidence correctness must be
adjudicated; matching source characters is insufficient. Exported agent reports
must be converted to this format using independently reviewed labels.

## Required for a publishable experiment

1. Verify source licenses and obtain a clinician-reviewed criterion dataset.
2. Freeze patient-and-trial-disjoint splits before prompt tuning.
3. Execute rules-only, standard RAG, uncontrolled-agent and bounded-agent arms
   with identical model version, retrieved context and matched budgets.
4. Execute temporal and missing-evidence ablations on the same test split.
5. Report coverage alongside false-assertion rate to expose abstention tradeoffs;
   include failures and measured token costs, never assume unmeasured cost is zero.
6. Perform patient-cluster uncertainty analysis and a held-out error review.
7. Compare against TrialGPT and other relevant prior work through a dated,
   reproducible literature review before claiming novelty.

Standard RAG and uncontrolled-agent experimental runners remain unimplemented;
their protocol entries are not executable baselines or measured results.
No model experiment, expert review or publication claim has been completed.
