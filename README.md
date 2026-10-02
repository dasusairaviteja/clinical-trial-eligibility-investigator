# Clinical Trial Eligibility Investigator

**Research project** — a single tool-using AI agent that investigates and verifies
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

Implementation authorized for routine automatic delivery. Initial environment foundation is available; clinical functionality is not implemented yet.

## Run locally

Python 3.12, no third-party packages or Azure credentials required:

```bash
python -m clinical_trial
python -m unittest discover -s tests -v
python scripts/check_repository.py
```

See `docs/ENVIRONMENTS.md` for GitHub Actions and `PROGRESS.md` for verified progress.


## Web workspace

From the repository root, run:

```bash
python -m http.server 8080 --bind 127.0.0.1 --directory web
```

Open http://localhost:8080. This is a local development server, not production
hosting. The responsive interface supports case selection, search/filtering,
evidence inspection, browser-local reviewer notes/history, and JSON export.
The screening case results are authored fictional examples, not model output.
There is no authentication or clinical backend yet; use synthetic records only.

### User-provided trial archive

```bash
python scripts/import_trials.py /path/to/clinical_dataset.zip --limit 200
```

Then open **Trial library**. The importer keeps only study metadata and eligibility
text; no files are extracted. It rejects DTD/entity declarations and caps record
size and preview count. Raw ZIPs and derived `web/local-trials.json` are ignored.
The library is a historical snapshot, separate from the fictional screening demo.
No claim is made that these studies are currently recruiting. Archive licensing
and redistribution terms remain unverified; do not publish the dataset.

Reviewed browser-local notes are not a secure or immutable audit trail.
