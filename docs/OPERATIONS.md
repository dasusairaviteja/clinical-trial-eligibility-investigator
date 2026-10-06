# Local operation and recovery

## Start

Python 3.12 is the application runtime. The default workflow uses only its
standard library and performs no network or paid model calls.

```sh
python -m clinical_trial.api examples/synthetic_sources.json
```

Open http://127.0.0.1:8000. Select **Investigate demo case**, inspect citations,
record a correction with a reason, then export the report and audit trail.
The separate older static demo remains in `web/index.html`; the API serves
`web/workspace.html`. Raw archive records are not loaded automatically.

## Optional Azure model

Set AZURE_OPENAI_ENDPOINT (HTTPS resource origin), AZURE_OPENAI_DEPLOYMENT, and
AZURE_OPENAI_API_KEY in the process environment using your normal secret tooling.
The application does not automatically read `.env`. Never paste keys into the UI.
Then explicitly opt in to paid calls with `--azure-model` on the command above.
The v1 adapter limits each output to 1,000 completion tokens, context to 100 KB,
each request to a 20-second timeout, and the agent to eight iterations. It records
provider token usage; USD cost is null until deployment-specific pricing is supplied.
Redirects are rejected to prevent forwarding credentials to another host.
No live model run has been executed in this release.

## Persistence

Reports and corrections live in ignored `local-data/reviews.db`. Corrections use
optimistic revision checks (HTTP 409 on stale writes) and preserve the original
report. Every accepted correction and revision update commits atomically.
Reviewer labels are self-declared; this local preview has no authenticated users.
The per-report hash chain is diagnostic only: a database owner can rewrite it.
It is not independently anchored or an immutable compliance record.

## Backup and restore

Use `ReviewStore('local-data/reviews.db').backup('backup.db')` from Python, or
SQLite's backup API from the official documentation. Do not copy a live database
file without coordinating writes. For restore, stop the application, preserve
the old database, restore the backup at the same path, and restart. Verify a known
report via GET /v1/reports/{id}. The automated recovery test opens a backup and
verifies report and audit equality. Backups must remain outside Git.

## Failure handling

- Missing/invalid registry: startup fails without printing source content.
- Invalid request/citation: HTTP 400 with no partial saved report.
- Stale review: HTTP 409; reload the current report before retrying.
- Database errors during writes: HTTP 503, transaction rolled back.
- Model errors or rejected actions: pending findings remain unknown.
- Tool budget exhaustion: no further tools run; unresolved criteria remain unknown.

## Production gate

Python's http.server is documented as unsuitable for production. This adapter
must not be exposed to the public internet. Required before Azure release:
production HTTP runtime, Entra authentication/authorization, authenticated audit
identities, persistent managed storage, rate limiting, telemetry, load testing,
backup retention and an actual ENG→TEST→PROD rollout/rollback rehearsal.
No Azure resources or application URLs were created by this release.

Official references checked 2026-10-06:
- https://docs.python.org/3.12/library/http.server.html
- https://docs.python.org/3.12/library/sqlite3.html
- https://learn.microsoft.com/en-us/rest/api/microsoft-foundry/azureopenai/chat

No third-party runtime dependency or new external dataset is introduced here.
Dataset redistribution licensing and clinical expert labeling remain unresolved.
