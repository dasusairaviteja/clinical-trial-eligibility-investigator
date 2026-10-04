# Implementation progress

## Increment 001 — environment foundation (2026-10-01)

Accepted locally: 1 point of the 100-point project (1% cumulative).
Acceptance: ENG/TEST/PROD recognized, invalid configuration rejected without
printing input, credential-free CLI, six tests passing, tracked dotenv guard,
and workflow defining each requested GitHub environment. Remote CI/environment
creation must be confirmed in the PR checks before merge.

No clinical agent, data ingestion, Azure deployment or research results yet.
This is AI-assisted implementation, reviewed and executed by the coding agent.

The existing BACKLOG.md contains a different phase allocation from the approved
conversation plan. Preserve it as prior planning history. Use this allocation
for future acceptance, without double counting: foundation/CI 8 (1 accepted),
data/contracts/ingestion 12, baselines/evaluation 12, agent/tools 18,
temporal/missing-evidence controls 14, reviewer UI/reports 10,
security/reliability/observability 10, deployment/recovery 8, research release 8.
Remaining foundation work: packaging/container setup, richer CI/security checks
and reproducible execution; phase is not complete.

Next increment: define evidence and criterion contracts, preserving exclusion
polarity and explicit unknown semantics. Expert labels and cloud budget remain
open decisions; neither blocks local foundation work.


## User-requested web workspace and dataset integration

Delivered outside the daily one-point cadence at the user's explicit request:
responsive static UI, case switching, evidence filtering, browser-local review
notes/history, JSON export, and a local XML ZIP importer with a trial-library view.
The uploaded archive contains 103,509 XML entries (2,835,555,965 bytes expanded),
no README or license entry. SHA-256:
`95b438339bc536235d68a983b1a4104c1b8444ea68b04ee8087c13fd738d91c0`.
A 200-record preview was imported locally; archive and derived records are excluded
from Git. Sample record NCT00000102 was last updated June 24, 2005: do not treat
recruitment status as current. This is trial metadata, not patient records.
No arbitrary new completion percentage is assigned to this UI addition; reassess
weighted acceptance when data contracts and the backend are connected. Preserve
the daily delivery cadence and resume with the next uncompleted backlog task.

Verification: nine Python tests passed; JavaScript syntax check passed. Browser
visual/interaction testing is not verified: Chromium installation failed in the
execution environment. Full browser QA remains a follow-up acceptance item.

## Increment 002 — evidence and criterion contracts (2026-10-02)

One point allocated from data/contracts/ingestion (12 total). Acceptance:
immutable, runtime-validated criteria, sources, citations and findings; six
inclusion/exclusion verdict mappings; rejection of absent/incorrect citations,
cross-patient sources, stale source versions, invalid offsets and unqualified
unknowns. Covered by 12 new test methods, alongside the 9 existing tests.

Cumulative weighted acceptance: 2/100 once this increment's checks pass.
The additional UI work remains unscored; this is not a claim of 2% clinical
accuracy or production readiness. Newer UI, TREC and configuration changes on
main are preserved. No model calls, raw dataset publication, or cloud spending.

Next: strict JSON case/report parsing and an integration boundary using these
contracts. The frontend currently retains its own deterministic demo evaluator;
these backend checks are not yet applied to UI output. Daily runs must read this
record and continue, not repeat increment 002.

## Increment 003 — strict case JSON and review reports (2026-10-02)

One additional point from data/contracts/ingestion: versioned strict JSON input,
bounded parsing, exact field and collection checks, duplicate-key rejection,
case/trial/patient linkage, complete one-to-one finding coverage, and deterministic
report generation using increment 002 evidence validation. A synthetic example
and `python -m clinical_trial.report` make this boundary runnable without Azure.

Acceptance: 13 new report/CLI test methods plus the existing 21 tests; no partial
report on failure, no raw input in errors, and no overall eligibility conclusion.
Cumulative weighted acceptance after passing checks: 3/100 (foundation 1/8,
data/contracts/ingestion 2/12). The earlier daytime increment is not repeated.

Next: connect case construction to trusted source lookup and a Python API;
then adapt the UI. Current UI exports are not this schema. No new dependencies,
external data publication, clinical effectiveness claims or Azure provisioning.

## Increment 004 — bounded local Python API (2026-10-03)

One additional point from foundation/CI: a dependency-free local HTTP adapter
exposes health and strict report-validation endpoints. It binds to loopback by
default, rejects unsupported media types, transfer encoding and oversized or
invalid bodies, uses generic non-echoing errors, suppresses request logging, and
adds no-store/browser hardening headers. Seven integration tests exercise the
server over TCP and preserve the existing report contract.

Acceptance requires the full local and GitHub CI suites to pass. Cumulative
weighted acceptance after those checks: 4/100 (foundation 2/8,
data/contracts/ingestion 2/12). This standard-library adapter is explicitly not
production hosting: authentication, TLS termination, rate limiting, durable
audit records and Azure deployment remain unimplemented. No clinical conclusion
is returned.

Next: construct cases from a trusted server-side source registry so callers
cannot supply both evidence and the evidence assertions being checked. The UI
still uses its independent demo schema and is not connected to this endpoint.
