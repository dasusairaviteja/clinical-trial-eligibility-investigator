# Acceptance ledger

Completion is accepted weighted backlog work. It is never test count, code volume,
or an estimate of clinical accuracy. The user accelerated delivery on 2026-10-06;
the former one-point daily target no longer limits implementation.

| Workstream | Total | Accepted after this PR passes | Evidence and remaining gate |
|---|---:|---:|---|
| Foundation/CI | 8 | 3 | Prior environment/API work (2); workspace CI and reproducible local execution (1). Packaging and production runtime pending. |
| Data/contracts/ingestion | 12 | 6 | Prior contracts/registries (4); conservative line parser with dates, hashes and source offsets (2). FHIR/Synthea adapter and live trial ingestion pending. |
| Baselines/evaluation | 12 | 3 | Polarity-aware metrics (1), leakage validator (1), cluster bootstrap (1). Executable matched RAG/uncontrolled baselines and real evaluation pending. |
| Agent/tools | 18 | 6 | Bounded injected-planner loop (2), validated tool dispatcher (2), mock-tested Azure adapter (2). Live provider acceptance and broader tasks pending. |
| Temporal/missing evidence | 14 | 3 | Calendar boundaries (1), explicit negative coverage (1), unit/missing-value checks (1). End-to-end temporal evidence binding and clinical cases pending. |
| Reviewer UI/reports | 10 | 3 | Integrated API investigation/report view (1), transactional corrections (1), export/audit access (1). Browser/accessibility QA and authenticated reviewer flow pending. |
| Security/reliability/observability | 10 | 2 | Request guards and allowlisted routes (1), tested SQLite backup and rollback/conflict behavior (1). Production auth, monitoring and load testing pending. |
| Azure deployment/recovery | 8 | 1 | Verified offline backup/restore CLI and audit integrity checks (1). Azure deployment and cloud recovery remain unaccepted. |
| Experiments/research release | 8 | 1 | Reproducible experiment protocol and explicit release gates (1). Expert labels, literature review, executed experiments and manuscript pending. |
| **Total** | **100** | **28** | **72 points remain unaccepted.** |

## Recovery increment — 2026-10-06

One additional point is accepted after this increment passes CI. All 83 Python
tests pass locally, including nine recovery tests covering round-trip restoration,
tampering, deleted history, overwrite prevention, partial-output cleanup,
concurrent source changes and read-only source access. This does not establish
cloud recovery, production readiness or externally anchored audit immutability.
Unfinished local WSGI/authentication drafts are excluded from this increment.

## Verification recorded for this change

74 Python tests pass locally; JavaScript syntax checks for both interfaces,
Python compilation, repository dotenv hygiene and diff whitespace checks pass.
The new HTTP integration tests exercise real loopback requests and SQLite writes.
Provider responses are mocked. No paid model request or Azure resource was used.
Browser launch failed because Chromium is absent; the attempted download also
failed. There is no verified screenshot or claim of visual/browser acceptance.

## External acceptance inputs

- Azure environment access, selected model deployment, model budget and production
  resource budget are required for live model/deployment validation.
- A qualified clinical reviewer and a licensed criterion-level labeled dataset
  are required for research conclusions. Current examples are fictional fixtures.
- A working browser test runtime is required for browser UX/accessibility checks.

Remaining software work is also explicitly listed above; these external inputs
are not the only remaining work. No section should be marked 100% merely because
its configuration file or protocol has been written.
