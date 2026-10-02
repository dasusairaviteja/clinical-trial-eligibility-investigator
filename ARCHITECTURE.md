# Architecture — Clinical Trial Eligibility Investigator

## Design principles
- Simplest architecture that satisfies the PRD.
- Single agent, small tool surface, no microservices.
- Deterministic business logic where possible; model only where judgment is needed.

## Components

```
Synthetic patient record (Synthea JSON)
        │
        ▼
┌─────────────────┐     ┌──────────────────────┐
│ Criteria        │     │ Patient history      │
│ retriever       │     │ inspector tools      │
│ (ClinicalTrials │     │ (record search,      │
│  .gov API)      │     │  timeline view)      │
└────────┬────────┘     └──────────┬───────────┘
         │                         │
         ▼                         ▼
┌─────────────────────────────────────────────┐
│ Eligibility agent (single tool-using agent) │
│  1. Parse each criterion                    │
│  2. Gather evidence via tools               │
│  3. Temporal check (dated events)           │
│  4. Classify: supported / contradicted /    │
│     unknown (abstain on missing evidence)   │
└──────────────────────┬──────────────────────┘
                       ▼
        ┌─────────────────────────┐
        │ Evidence-linked report  │
        │ + missing-info checklist│
        └─────────────────────────┘
```

### 1. Criteria retriever
- **What:** Fetches inclusion/exclusion criteria for a trial ID from
  ClinicalTrials.gov API v2.
- **Why:** Criteria are the ground truth the patient is judged against.
- **Failure behavior:** API down → run fails fast with a clear error; criteria
  are cached per trial ID for reproducibility.

### 2. Patient history inspector tools
- **What:** Read-only tools over the synthetic record: search by code/keyword,
  list dated clinical events (conditions, meds, procedures) as a timeline.
- **Why:** The agent must look at evidence, not rely on parametric memory.
- **Failure behavior:** Missing record section → tool returns "not found", which
  the agent treats as missing evidence (→ unknown), never as negative evidence.

### 3. Eligibility agent
- **What:** One agent loop: for each criterion, plan evidence gathering, call
  tools, apply temporal logic, classify.
- **Why Level 3 fits:** A bounded investigation task with verifiable outputs.
- **Guardrails:** iteration cap per criterion, no network beyond the approved
  APIs, every classification must cite evidence or be marked unknown.

### 4. Temporal reasoning
- **What:** Date arithmetic over the event timeline ("within 6 months of
  enrollment date").
- **Why:** The research hypothesis — ordinary RAG ignores time and gets these wrong.

### 5. Report generator
- **What:** Deterministic template rendering: per-criterion verdict + evidence
  quotes + checklist of unknowns.
- **Why:** Deterministic rendering keeps the model from embellishing verdicts.

## Data
- Synthetic patients from Synthea (generated locally, seeded).
- Trial criteria from ClinicalTrials.gov (public).
- Nothing real, nothing governed, nothing committed that isn't synthetic/public.

## Environments
- GitHub environments ENG / TEST / PROD exist for CI/CD gating.
- Azure deployment (AKS or Container Apps) deferred — user will deploy later.
  When that happens: `azure/login` with federated credentials per environment,
  secrets as environment-scoped GitHub secrets.

## Security notes
- No PHI. Synthetic data only — still, treat the pipeline as if data were
  sensitive (no full-record logging).
- `.env` gitignored; CI secrets-guard job fails the build if committed.
- Agent tools are read-only; no side effects to model.

## Alternatives considered
- Ordinary RAG over the record: kept as the *baseline* to beat, not the design.
- Multi-agent team: rejected — Level 3 specifies a single agent; added
  coordination cost with no justified benefit.
