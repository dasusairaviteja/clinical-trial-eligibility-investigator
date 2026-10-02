# PRD — Clinical Trial Eligibility Investigator

## Problem
Matching patients to clinical trials is slow, manual, and error-prone. Reviewers
read long eligibility criteria lists and cross-check them against fragmented
patient histories. Under time pressure, reviewers assert eligibility on weak or
missing evidence — a safety and compliance risk.

## Product
A single tool-using AI agent that investigates a (synthetic) patient record
against a trial's eligibility criteria and produces a reviewer-ready report.

## Workflow
1. Import a synthetic patient record.
2. Retrieve the trial's eligibility criteria.
3. Inspect relevant patient history via tools.
4. Classify each criterion as **supported**, **contradicted**, or **unknown**.
5. Emit an evidence-linked reviewer report.
6. Emit a missing-information checklist for the human reviewer.

## Users
- Primary: clinical research coordinators / reviewers (draft report consumers).
- Secondary: researchers studying eligibility automation.

## Requirements
- FR-1: Ingest synthetic patient records (Synthea format).
- FR-2: Fetch trial eligibility criteria (ClinicalTrials.gov API).
- FR-3: Per-criterion classification: supported / contradicted / unknown.
- FR-4: Every classification links to the evidence (record excerpt or criterion
  text) that justifies it.
- FR-5: Unknown classifications produce a missing-information checklist item.
- FR-6: Temporal criteria (e.g. "no chemotherapy within 6 months") are evaluated
  against dated events, not just keyword presence.
- FR-7: The agent must abstain (unknown) rather than guess when evidence is absent.
- NFR-1: No real patient data anywhere in the repo, CI, or logs.
- NFR-2: Secrets in `.env` only; `.env` is gitignored and CI rejects it.
- NFR-3: Deterministic, reproducible runs (seeded synthetic data, pinned deps).
- NFR-4: Cost per case is measured and reported.

## Research hypothesis
Explicit handling of missing information and temporal constraints reduces
incorrect eligibility assertions compared with ordinary RAG.

## Evaluation (summary; see EVALUATION.md)
Criterion-level accuracy, false eligibility assertions, evidence correctness,
abstention quality, cost per case. Baselines: ordinary RAG without explicit
unknown-handling. Ablations: temporal reasoning on/off, abstention calibration
on/off.

## Out of scope
- Real patient data (MIMIC-IV or otherwise) — credentialed and governed, never
  committed here.
- Medical advice or autonomous enrollment decisions — output is a draft for
  qualified human review only.
- Multi-agent orchestration — single agent by design (Level 3 constraint).

## Success criteria
- Agent classifies criteria with evidence links on synthetic cases.
- Measured reduction in false eligibility assertions vs. the RAG baseline.
- Reproducible: fresh clone + `.env` → same results.
- Deployed to ENG/TEST/PROD (Azure deployment deferred per user).

## Open decisions (need user input)
- Reviewer persona and availability of clinical expert input for label review.
- "9 PM EST" push cadence: fixed UTC-5 vs America/New_York (observes EDT).
