# Acceptance ledger

Completion is accepted weighted backlog work. It is never test count, code volume,
or an estimate of clinical accuracy. The user accelerated delivery on 2026-10-06;
the former one-point daily target no longer limits implementation.

| Workstream | Total | Accepted after this PR passes | Evidence and remaining gate |
|---|---:|---:|---|
| Foundation/CI | 8 | 6 | Hash-pinned Gunicorn runtime, reproducible install and real runtime CI smoke (+3); container deployment still pending. |
| Data/contracts/ingestion | 12 | 9 | Offline trial mapping, explicit reviewed promotion and synthetic observation adapter (+3); FHIR/Synthea and live ingestion pending. |
| Baselines/evaluation | 12 | 6 | Executable research arms, common operational caps and paired-case checks (+3); live runs, token matching and expert adjudication pending. |
| Agent/tools | 18 | 9 | Ranked chunk retrieval, context/deadline controls and enforced source-bound check dispatch (+3); live provider and broader tasks pending. |
| Temporal/missing evidence | 14 | 7 | Source-bound threshold/date/unit and event coverage/conflict controls (+4); clinical validation and broader temporal language pending. |
| Reviewer UI/reports | 10 | 5 | Token access and latest-reviewer-assertion display with DOM contracts (+2); real browser/accessibility QA pending. |
| Security/reliability/observability | 10 | 6 | Individual auth, rate/capacity limits, privacy-preserving telemetry and adversarial request tests (+4); TLS proxy, identity federation and load/security testing pending. |
| Azure deployment/recovery | 8 | 1 | Verified offline backup/restore CLI and audit integrity checks (1). Azure deployment and cloud recovery remain unaccepted. |
| Experiments/research release | 8 | 1 | Reproducible experiment protocol and explicit release gates (1). Expert labels, literature review, executed experiments and manuscript pending. |
| **Total** | **100** | **50** | **50 points remain unaccepted.** |

## Milestone 50 — 2026-10-06

See MILESTONE_50.md for the 22-point acceptance breakdown, exact checks and
remaining limits. Acceptance requires CI success on this milestone commit.
108 Python tests, DOM contracts and real Gunicorn smoke pass locally.

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
