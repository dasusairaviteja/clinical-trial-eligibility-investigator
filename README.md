# Clinical Trial Eligibility Investigator

**Level 3 research project** — a single tool-using AI agent that investigates and verifies
whether a patient is eligible for a clinical trial.

## What it does

Matching a patient to a trial requires interpreting many eligibility criteria,
incomplete records, and time-dependent conditions. This agent:

1. Imports a **synthetic patient record**
2. Retrieves **trial eligibility criteria** (ClinicalTrials.gov)
3. Inspects the relevant patient history with tools
4. Marks each criterion as **supported**, **contradicted**, or **unknown**
5. Produces an **evidence-linked report** plus a **missing-information checklist** for a human reviewer

## Research hypothesis

Explicit handling of missing information and temporal constraints reduces
incorrect eligibility assertions compared with ordinary RAG.

## Key constraints

- **No real patient data.** Synthetic records only (Synthea). Nothing here is
  medical advice; every output is a draft for qualified human review.
- **Secrets** (API keys, Azure credentials) live in `.env`, which is gitignored
  and never committed.

## Repository layout

- `PRD.md` — product requirements (reviewable)
- `ARCHITECTURE.md` — system architecture
- `EVALUATION.md` — evaluation protocol, baselines, metrics, ablations
- `BACKLOG.md` — weighted backlog totaling 100%
- `src/` — application code (after scope approval)
- `tests/` — tests
- `docs/` — research documentation

## Status

Scope pending user approval. No implementation yet.
