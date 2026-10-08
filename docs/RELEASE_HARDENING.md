# Release hardening — 2026-10-08

The request to complete 100/100 does not waive acceptance evidence. This change
adds four points to the previously verified 75, conditional on every relevant CI
check passing. Implementation is AI-assisted and requires qualified review.

| Workstream | Added | Acceptance evidence |
|---|---:|---|
| Agent/tools | 1 | Offline investigator now executes the same trusted, source-bound dated measurement and event checks as the agent, with a validated per-criterion budget and provenance-validated reports. |
| Temporal/missing evidence | 1 | Malformed structured evidence, duplicate JSON keys, mismatched patient IDs and invalid coverage cannot be silently discarded in favor of a convenient record; regression tests cover both source orders. |
| Reviewer UI/reports | 1 | Keyboard skip navigation and automated WCAG 2/2.1 A/AA scans on connected, investigated and corrected screens, verified in actual Chromium CI. |
| Security/reliability | 1 | Report/audit snapshot consistency under an interleaved writer, UI response isolation after disconnect, and actual Gunicorn concurrency/replay/conflict verification. |

## Reproduce

```bash
python -m pip install --require-hashes -r requirements.txt
python -m unittest discover -s tests -v
node scripts/test_workspace.js
python scripts/smoke_runtime.py
python scripts/check_concurrent_runtime.py
npm ci --ignore-scripts
npx playwright install --with-deps chromium --only-shell
npm run test:browser
```

Local evidence: 141 Python tests passed. The 24-request, four-client synthetic
probe returned seven successful reports and seventeen intentional busy responses
(503). Measured p50 was 1.705 ms and p95 9.489 ms for all responses, including busy
responses. Successful idempotent replay returned the identical report; a changed
payload with the same key returned 409. These measurements are one local run,
not a capacity promise, production load acceptance, or model latency benchmark.
The probe prints fresh measurements in CI and never makes paid model requests.

The strict evidence policy can increase abstention: an unparseable structured
source blocks an assertion because it cannot safely be classified as irrelevant.
Well-formed observations from other dates remain irrelevant. Undated legacy age
rules are still demo-only; research requiring time alignment must use dated rules.
No generic clinical-language entailment or clinical unit conversion is inferred.

Automated accessibility is not full WCAG conformance. Screen-reader, magnification
and representative reviewer sessions remain required. Dependency selection was
checked against the official Playwright accessibility guide and Deque package
metadata on 2026-10-08. `@axe-core/playwright` 4.13.0 is pinned as a dev dependency;
its license is MPL-2.0. It is not shipped in the application container.

- https://playwright.dev/docs/accessibility-testing
- https://github.com/dequelabs/axe-core-npm/tree/develop/packages/playwright
- https://www.npmjs.com/package/@axe-core/playwright

## Remaining 21 points: evidence needed before 100/100

| Workstream | Points | Outstanding acceptance |
|---|---:|---|
| Data | 1 | Verify public trial access/terms and run a traceable real ingestion acceptance case. The uploaded historical archive has no verified redistribution license. |
| Evaluation | 2 | Run actual token-matched comparisons and qualified reviewer adjudication with patient/trial-disjoint data. |
| Agent | 5 | Broader supported-criterion acceptance and live model planning, failure and budget behavior on approved fixtures; preflight input-budget control remains incomplete. |
| Temporal | 2 | Broader clinical temporal language/ambiguity acceptance with expert-reviewed labels. |
| Reviewer | 1 | Manual accessibility and representative reviewer usability acceptance. |
| Security | 1 | Independent security review and deployment-representative load/operational acceptance. |
| Azure | 4 | Install and expose the authenticated app securely; verify ENG/TEST/PROD deployment, operational monitoring and cloud recovery. Current Bicep provisions private compute only. |
| Research | 5 | Licensed/adjudicated study, real baseline/ablation runs, reproducible artifacts and supported manuscript conclusions/research release review. |

Required inputs: an accessible Azure subscription/model deployment and approved
spending limits; deployment network/TLS settings; a qualified clinical reviewer
and licensed study data; participants for manual usability testing. No Azure CLI,
configured model environment variables or repository `.env` was available during
this work. No secret values were read. Local software development was not blocked
by missing credentials, but live acceptance cannot be substituted with mocks.

Further software work also remains (notably broader language support, strict
preflight model input budgeting and host/TLS deployment). Those items are not
being relabeled as complete or as purely credential blockers. There is no
verified ENG, TEST or PROD application URL and no publishable efficacy result.
