# Acceptance ledger

Completion is accepted weighted backlog work. It is never test count, code volume,
or an estimate of clinical accuracy. The user accelerated delivery on 2026-10-06;
the former one-point daily target no longer limits implementation.

| Workstream | Total | Accepted after this PR passes | Evidence and remaining gate |
|---|---:|---:|---|
| Foundation/CI | 8 | 8 | Container build and isolated runtime smoke; production base-image digest pin remains an operational gate. |
| Data/contracts/ingestion | 12 | 11 | Synthetic FHIR Observation subset with provenance/rejection controls; live ingestion acceptance remains. |
| Baselines/evaluation | 12 | 10 | Component-disjoint assignment and exact adjudication joins; live token-matched and expert-adjudicated evaluation remains. |
| Agent/tools | 18 | 14 | Reported usage, completion/call caps and sanitized provider failure categories; broader/live model acceptance remains. |
| Temporal/missing evidence | 14 | 13 | Dated age and inclusive measurement ranges added; broader temporal language and clinical validation remain. |
| Reviewer UI/reports | 10 | 9 | Saved history, escaped printable reports and Chromium workflow/mobile smoke; accessibility and broader usability acceptance remain. |
| Security/reliability/observability | 10 | 9 | Caller-scoped durable request replay and concurrent reservation controls; independent security/load review remains. |
| Azure deployment/recovery | 8 | 4 | Local recovery plus compiled VM template, environment separation and budget-gated what-if/deployment command; no live cloud deployment. |
| Experiments/research release | 8 | 3 | Protocol, synthetic regression and deterministic release inventory; actual research conclusions and manuscript remain. |
| **Total** | **100** | **81** | **19 points remain unaccepted.** |

## Local research completion increment — 2026-10-08

Two points are conditional on this PR passing CI and merging: bounded explicit
all/any rule composition (agent/tools +1), and source-bound elapsed-day windows
(temporal +1). Existing month/measurement and polarity contracts remain enforced.
See LOCAL_COMPLETION.md for the complete increment, verification and remaining
acceptance gates. Cohort/review tooling and manuscript preparation are useful
software deliverables, not completed model studies or clinical validation.

## Release hardening — 2026-10-08

Four additional points are conditional on this PR passing all CI checks. See
RELEASE_HARDENING.md for evidence and the exact remaining 21-point breakdown.
141 Python tests, DOM contracts, actual Gunicorn smoke and bounded concurrent
requests pass locally. Chromium accessibility and disconnect-race checks run in CI.
No Azure deployment, clinical validation or live-model result is implied.

## Milestone 75 — 2026-10-07

Twenty additional points are conditional on all PR checks passing, including actual
Chromium/container smoke and Bicep compilation in GitHub CI. See MILESTONE_75.md.
Local Python suite: 136 passing tests. No live deployment or clinical result claimed.

## Milestone 55 — 2026-10-06

Five additional points: two ablation controls, paired outcome comparison, seeded
paired uncertainty, and a reproducible synthetic regression study. See MILESTONE_55.md.
Acceptance requires CI success. No clinical or live-model performance is claimed.

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
- Manual assistive-technology and representative reviewer usability testing remain
  required beyond the automated Chromium accessibility scans.

Remaining software work is also explicitly listed above; these external inputs
are not the only remaining work. No section should be marked 100% merely because
its configuration file or protocol has been written.
