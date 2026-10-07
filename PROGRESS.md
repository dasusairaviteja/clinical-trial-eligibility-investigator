# Milestone 55 — 2026-10-06

Added five research-workflow acceptance points; cumulative 55/100 after passing CI.
Implemented isolated temporal/missing-evidence ablations, paired metrics and seeded
patient-cluster intervals. Executed and committed a six-case synthetic control
study with a scripted planner (not an LLM experiment). 117 Python tests and DOM
checks pass. Runtime smoke initially blocked by missing Gunicorn; reinstall of the
hash-pinned dependency resolved it and the smoke rerun passed. The comparison CLI,
compilation, hygiene and whitespace checks also pass. See docs/MILESTONE_55.md.
Next: deployment packaging and browser QA; live model/clinical validation remain.

# Milestone 50 — 2026-10-06

Added 22 weighted software acceptance points; cumulative 50/100 after CI passes.
See docs/MILESTONE_50.md for per-item evidence and remaining requirements.
Validation: 108 Python tests, workspace DOM contracts, actual Gunicorn process
smoke, offline rules runner, compilation, JS syntax, hygiene and whitespace checks.
No paid calls, resources or clinical data. No browser acceptance claimed.
Next: deployment packaging, browser QA, live ingestion and experiment ablations.

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

## Increment 005 — trusted evidence registry boundary (2026-10-04)

One additional point from data/contracts/ingestion: API requests now carry only
version-pinned source references. An immutable, operator-loaded registry resolves
the exact synthetic patient snapshots before existing citation checks run. Strict
registry/request parsing rejects caller-supplied text, unknown patients, missing
or stale versions, duplicate snapshots/references, extra fields and malformed
JSON without echoing record content. A split fictional example demonstrates the
trust boundary without publishing real patient data.

Acceptance requires five registry tests, the updated API integration suite and
all earlier checks to pass locally and in GitHub Actions. Cumulative weighted
acceptance after those checks: 5/100 (foundation 2/8,
data/contracts/ingestion 3/12). This establishes provenance lookup, not semantic
entailment, authentication, record completeness, or clinical eligibility.

Next: define a trusted trial-criterion registry so both evidence and eligibility
criteria are independently versioned rather than supplied by the caller. The UI
remains disconnected from this research API.

## Increment 006 — trusted versioned trial criteria (2026-10-05)

One additional point from data/contracts/ingestion: the trusted registry now owns
versioned trial snapshots and their ordered inclusion/exclusion criteria. API
requests provide only a trial ID/version reference plus findings; caller-provided
criterion wording, polarity, membership and ordering are rejected as extra input.
Unknown or stale trial versions, duplicate trial snapshots, cross-trial criteria
and duplicate criterion IDs fail closed before a report is generated.

Acceptance requires the expanded registry and API suites plus all prior checks to
pass locally and in GitHub Actions. Cumulative weighted acceptance after those
checks: 6/100 (foundation 2/8, data/contracts/ingestion 4/12). The fictional
example registry is not current ClinicalTrials.gov data, and no claim of semantic
criterion parsing, recruitment status, or clinical eligibility is made.

Next: add a deterministic, provenance-preserving criterion ingestion transform
for public trial records, with explicit snapshot dates and parser failure output.

## Accelerated implementation — 2026-10-06

The user requested full delivery, superseding the one-point-per-day pace.
Added conservative criterion parsing, numerical/calendar tools, a bounded single
agent and mock-tested Azure planner, offline investigation, a connected local web
workspace, transactional SQLite corrections/audit export, backup recovery tests,
and an evaluation harness with leakage checks and patient bootstrap uncertainty.
No secrets or patient dataset contents were added. Implementation is AI-assisted.

74 local Python tests pass. Both JavaScript syntax checks, compileall, repository
hygiene and whitespace checks pass. Browser QA was attempted but Chromium launch
and download failed. Live Azure/model checks were not run.

After CI passes, weighted accepted progress is 27/100 (+21), with exact allocation
and outstanding gates in docs/ACCEPTANCE.md. This is NOT 100/100. Additional code,
production validation, expert labels and reproducible research experiments remain.
Next: production service/authentication and executable matched-baseline runners;
do not keep creating one-point registry-only increments.
# Recovery increment — 2026-10-06

- Added verified offline backup/restore and audit integrity CLI.
- Read-only source access, exclusive destination creation, owner-only permissions,
  integrity/hash/revision checks, and failed-output cleanup.
- Validation: 83 Python tests passed (nine new recovery tests).
- Accepted progress after CI: +1 point, cumulative 28/100.
- Azure deployment, authenticated production runtime, browser QA, remaining data
  adapters, baseline runs and research validation remain incomplete.
- Next: finish and test the authentication/runtime drafts, then deployment artifacts.
