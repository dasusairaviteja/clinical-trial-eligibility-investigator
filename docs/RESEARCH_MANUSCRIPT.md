# Temporal and missing-evidence controls for trial screening support

Status: methods draft, not a completed paper. No novelty or efficacy claim.
AI assistance was used for implementation and drafting. Authors must verify all
methods, sources, results and submission policies before publication.

## Question and falsifiable hypothesis

Does a bounded agent with deterministic temporal checks and explicit missing-data
abstention reduce false no-barrier assertions compared with ordinary RAG, while
retaining useful coverage? The hypothesis fails if a held-out comparison shows no
reliable reduction, or if the reduction is explained by unacceptable abstention.
A domain expert must set the minimum acceptable coverage before seeing results.

## Related work: initial screening, checked 2026-10-08

This is a starting bibliography, not a systematic or exhaustive literature review.

| Work | Verified relevance | Required comparison |
|---|---|---|
| Matching patients to clinical trials with large language models (TrialGPT), Nature Communications, 2024; DOI 10.1038/s41467-024-53081-z | NLM describes retrieval, criterion-level matching and trial ranking. | Compare criterion decisions and evidence on a common dataset; do not compare incompatible headline scores. |
| PRISM: Patient Records Interpretation for Semantic clinical trial Matching system using large language models, npj Digital Medicine, 2024; DOI 10.1038/s41746-024-01274-7 | Evaluates trial matching on real-world EHRs and describes OncoLLM. | Test generalization beyond short synthetic cases and preserve insufficient-information labels. |
| TrialMatchAI: an end-to-end AI-powered clinical trial recommendation system to streamline patient-to-trial matching, Nature Communications, 2026; DOI 10.1038/s41467-026-70509-w | Publisher search abstract describes a modular system using fine-tuned open-source models. Full methods were not assessed here. | Review full methods, licensing and evaluation before selecting it as a reproducible comparator. |

Primary sources:
- https://www.ncbi.nlm.nih.gov/research/trialgpt/about/
- https://www.nature.com/articles/s41467-024-53081-z
- https://www.nature.com/articles/s41746-024-01274-7
- https://www.nature.com/articles/s41467-026-70509-w

A useful application is not itself a publishable contribution. The proposed
contribution must demonstrate a reproducible safety/coverage effect attributable
to the controls. Existing criterion-level and insufficient-information approaches
mean novelty cannot be inferred from the presence of an agent or citations.

## Methods to freeze before a study

Use licensed synthetic patient records and versioned public trial records. Record
provenance, label instructions and cohort selection/exclusion reasons. Split by
connected patient/trial components to prevent both forms of overlap. Hold test
data apart before tuning. Obtain independent clinical labels and adjudicate
disagreements; fixture labels are not clinical gold standards.

Run rules-only, standard RAG, uncontrolled-agent and bounded-agent conditions,
then remove temporal and missing-evidence controls separately. Freeze model
version, prompts, retriever and input snapshots. Match budgets and report actual
input/output tokens, failed calls and unpriced costs. Current call/byte limits
are implemented; live matched-token acceptance remains outstanding.

Primary outcome: false no-barrier assertions per criterion, with coverage reported
beside it. Also report conditional false-assertion rate, macro-F1, adjudicated
evidence accuracy, latency and cost. Use paired uncertainty at the patient level;
shared-trial dependencies require further statistical treatment. Predefine any
coverage margin, sample-size justification and multiple-comparison correction.

## Results

No clinical or live-model results are available. The repository's synthetic study
tests engineered control behavior using a scripted planner. It cannot establish
medical accuracy, clinical benefit or superiority to prior work. Populate results
only from frozen, reproducible, independently reviewed experiment artifacts.

## Limitations and release

The executable rule grammar is narrow. Unsupported clinical language abstains.
Data completeness is operator-asserted, not independently verified. Multiple
matching observations conservatively trigger unknown. Clinical unit conversion,
general temporal-language interpretation and causal clinical reasoning are absent.
Reviewer corrections remain assertions, not automatic ground truth.

Release code, configurations, seeds, hashes, raw prediction outputs where licensed,
adjudication protocol and exact analysis commands. Do not publish patient records,
secrets, restricted trial attachments or private review mapping files. Obtain
appropriate data-use and institutional determinations for any future clinical
study. This project does not make enrollment decisions or contact patients.
