# Milestone 75 acceptance

Twenty additional points build on the accepted 55. Accept only after the exact PR
head passes Python, browser, container and Bicep CI checks.

| Workstream | Added | Evidence |
|---|---:|---|
| Foundation/CI | 2 | Allowlisted container build (1); non-root, read-only-root container smoke with real investigation/storage (1) |
| Data/contracts/ingestion | 2 | Synthetic FHIR R4 quantitative Observation mapping (1); patient/coding/unit/status/time/provenance controls and rejection tests (1) |
| Baselines/evaluation | 2 | Connected-component patient/trial split assignment (1); exact, reviewer-attributed adjudication join with leakage/mismatch tests (1) |
| Agent/tools | 3 | Verified provider usage accumulation (1); aggregate completion and call caps (1); sanitized rate-limit/transport error categories that fail closed (1) |
| Temporal/missing evidence | 2 | Dated age assessment (1); inclusive measurement range rules (1), using source-bound checks |
| Reviewer UI/reports | 3 | Bounded saved-report history (1); escaped standalone printable report (1); actual Chromium desktop workflow and mobile-overflow smoke (1) |
| Security/reliability/observability | 2 | Durable caller-scoped request deduplication (1); concurrent reservation/body-conflict and failure-release tests (1) |
| Azure deployment/recovery | 3 | Compiled private-VM infrastructure artifact (1); separate ENG/TEST/PROD mappings (1); budget-gated deployment command with what-if default and environment validation (1) |
| Experiments/research release | 1 | Deterministic SHA-256 source release inventory generated in CI |
| **Total added** | **20** | **75/100 after all gates pass** |

Local evidence: 136 Python tests and DOM contracts pass. Local Chromium download
failed; Docker and Bicep are not installed here. Those three checks run in GitHub
CI and must pass before this milestone is accepted. No live Azure deployment is
implied by template compilation. No paid model calls or clinical data were used.

## Remaining 25 points and material limitations

The system still needs live public-data ingestion acceptance, broader real-model
evaluation, token-matched experiments, expert evidence adjudication, clinical
validation, production security/load testing, actual Azure deployment and recovery,
and research release review. Browser smoke tests are not an accessibility audit.

FHIR support is a strict subset, not full Synthea interoperability. It requires
explicit synthetic attestation and an operator-approved code/unit map. Unsupported
entries produce issues. Calendar dates preserve the record's explicit timezone
date; no date inference or clinical equivalence inference occurs.

Provider budgets cap calls and requested output tokens. Input-token stopping uses
reported usage after a response; it is not a guaranteed preflight aggregate input
cap. Malformed/missing usage blocks subsequent calls. No automatic paid retries.

Deduplication requires Idempotency-Key on POST /v1/investigate. A matching successful
retry returns the saved report; mismatched bodies or concurrent reservations return
409. Keys are scoped to reviewer identity. A process crash can leave a pending
reservation; operators must reconcile it rather than automatically rerun. This
does not guarantee exactly-once external model charges or deduplicate corrections.
The browser does not automatically retry failed investigations.

Azure artifacts provision private compute only. They do not configure TLS, publish
an application, install the container, grant data access or create secrets. The VM
has no public IP and inbound traffic is denied except explicitly scoped management
SSH. Existing subnet, private management access, pinned Ubuntu image version and
budget approval are prerequisites. Host deployment/TLS and cloud recovery remain
unaccepted. The Docker base tag is floating; record/pin its resolved digest before
production promotion. No production-ready claim is made.
