# Evaluation protocol — Clinical Trial Eligibility Investigator

## Hypothesis
Explicit handling of missing information and temporal constraints reduces
incorrect eligibility assertions compared with ordinary RAG.

## Metrics
| Metric | Definition |
|---|---|
| Criterion-level accuracy | % of criteria classified correctly (supported/contradicted/unknown) |
| False eligibility assertions | % of criteria marked supported/contradicted on insufficient evidence |
| Evidence correctness | % of cited evidence spans that actually support the verdict |
| Abstention quality | precision/recall of the "unknown" class |
| Cost per case | USD per patient-trial evaluation (tokens + API calls) |

## Datasets
- **Patients:** Synthetic records generated with Synthea (seeded, versioned).
- **Trials:** Real public eligibility criteria from ClinicalTrials.gov.
- **Labels:** Per-criterion gold labels. NOTE: credible clinical conclusions
  require expert-reviewed labels — initial labels are author-reviewed and
  marked provisional until a clinical reviewer validates them.

## Baselines
1. **Ordinary RAG:** chunk the record, retrieve top-k per criterion, classify —
   no explicit unknown handling, no temporal logic.
2. **RAG + abstention prompt:** same retrieval, instructed to say unknown when unsure.

## Ablations (isolate the contribution)
- A: temporal reasoning on/off.
- B: calibrated abstention (evidence threshold) on/off.
- C: evidence-link requirement on/off.

## Experiment config
- `experiments/baseline_rag.yaml`, `experiments/agent_full.yaml`,
  `experiments/ablation_*.yaml` — model, seed, dataset version, thresholds.
- Every run logs: config hash, dataset version, metric table, cost.

## Related work
- TrialGPT (patient-to-trial matching): existing system — our contribution must
  isolate a measurable improvement (temporal reasoning, calibrated abstention),
  not re-implement matching. Literature review will confirm the gap before any
  publication claim.

## Acceptance bar (proposed, needs user sign-off)
- False eligibility assertions: ≥30% relative reduction vs baseline RAG.
- Evidence correctness: ≥90% of citations valid.
- Cost per case: reported, no fixed cap yet.
