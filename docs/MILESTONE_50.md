# Milestone 50 acceptance protocol

This milestone adds 22 weighted points to the accepted 28. Points describe tested
software capabilities, not clinical accuracy, publication readiness or deployment.
Accept this table only after CI passes on the exact PR head.

| Workstream | Added | Acceptance evidence |
|---|---:|---|
| Foundation/CI | 3 | Gunicorn WSGI runtime (1), hash-pinned install (1), real process startup/auth/investigate/persistence smoke in CI (1) |
| Data/contracts/ingestion | 3 | Offline v2-shaped trial adapter (1), hash/offset-preserving explicit review promotion with tamper/unparsed rejection (1), validated synthetic observation adapter (1) |
| Baselines/evaluation | 3 | Executable rules/RAG arms (1), uncontrolled/bounded comparison arms under common caps (1), paired-case identity checks and raw artifact CLI (1) |
| Agent/tools | 3 | Ranked chunk retrieval with original offsets (1), context/deadline/call bounds (1), source-bound check dispatch and enforced submission (1) |
| Temporal/missing evidence | 4 | Trusted criterion supplies measurement threshold (1), exact assessment date/unit binding (1), event-history window binding (1), complete negative window and conflicting-source abstention tests (1) |
| Reviewer UI/reports | 2 | Token connection/disconnection UI (1), latest reviewer assertion displayed alongside preserved original (1); tested DOM contracts |
| Security/reliability/observability | 4 | Individual reviewer token authentication and identity binding (1), rate/concurrency bounds (1), request-ID/status/duration-only telemetry (1), negative auth/body/route/security-header tests (1) |
| **Total added** | **22** | **50/100 cumulative after passing CI** |

Verification: 108 Python tests, workspace DOM contracts, actual Gunicorn subprocess
smoke, offline rules artifact command, Python compilation, JavaScript syntax,
repository dotenv hygiene, diff whitespace and targeted secret-pattern inspection.
Model providers remain mocked. Browser rendering and accessibility audits remain
unaccepted. An existing partial-quote positive agent test now uses the complete
source-bound assessment; wrong-verdict citations are explicitly rejected.

## Limits retained for the remaining 50 points

- No Azure deployment, application URL, cloud recovery drill or paid resource.
- Runtime requires TLS/buffering proxy before public use. One process, one local
  SQLite database, one shared research workspace. All configured reviewers can
  access all reports; no tenant isolation or production identity federation.
- The small synthetic observation schema is not FHIR/Synthea support. Public
  study-shaped input mapping is fixture-tested, not live-ingestion acceptance.
  Dataset licensing and public redistribution approval remain unresolved.
- Only explicit rule grammars are enforced. Legacy age text has no assessment
  date and must not be treated as a current clinical assessment. Event coverage
  comes from an operator-approved source; it cannot prove real-world completeness.
- Model response timeout is adapter-controlled; runtime deadline checks occur
  before and after each synchronous model call, not via forced cancellation.
- Experiment arms have common maximum calls and context bytes, not demonstrated
  equal consumed tokens/cost. Uncontrolled means no deterministic evidence gate;
  it still has provenance checks and operational limits. Model-specific token
  accounting, temporal/missing-evidence ablations, repeated-seed studies and
  blinded expert adjudication remain. No efficacy claim or publication claim.
- Browser QA, load testing, security review, package/container deployment,
  externally anchored audits and live provider acceptance remain required.

## Reproduce

```sh
python -m pip install --require-hashes -r requirements.txt
python -m unittest discover -s tests -v
node scripts/test_workspace.js
python scripts/smoke_runtime.py
python -m clinical_trial.experiments examples/synthetic_sources.json examples/synthetic_request.json local-data/rules-run.json
```

The last command requires an existing output directory and a new output filename.
It produces measured latency and raw predictions, not adjudicated research scores.
