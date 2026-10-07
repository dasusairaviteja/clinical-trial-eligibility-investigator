# Authenticated research runtime

Install the hash-pinned requirements, then configure `REVIEWER_TOKENS_JSON` as a
JSON mapping from individual randomly generated tokens (at least 32 characters)
to reviewer identifiers. Supply this through your shell's secure environment or
a secret manager. Never put real credentials in documentation, commands committed
to GitHub, screenshots or examples. Generate strong tokens with
`secrets.token_urlsafe(32)`. Length validation alone does not establish entropy.

```sh
python -m pip install --require-hashes -r requirements.txt
python -m gunicorn -c gunicorn.conf.py --bind 127.0.0.1:8000 'clinical_trial.wsgi:create_app()'
```

Open http://127.0.0.1:8000 and connect with your reviewer token. It is held in page
memory only and cleared by disconnect/reload. The server binds correction identity
to the credential, ignoring any reviewer label submitted by the client. These are
bearer credentials, not an SSO system; rotate by changing the environment and
restarting. Do not share tokens. All authorized reviewers share one workspace.

`REGISTRY_PATH` defaults to `examples/synthetic_sources.json` and `REVIEW_DATABASE`
to `local-data/reviews.db`. `ENABLE_AZURE_MODEL=true` opts into paid Azure calls;
leave it unset for offline use. No dotenv file is automatically loaded. Guard the
data directory using operating-system permissions and encrypted storage.

Deployment requires a TLS-terminating buffering proxy; never expose plain HTTP
tokens on a network. The checked configuration uses one worker and four threads.
Limits are per process: 60 authenticated requests per reviewer per minute, two
concurrent investigations, 1MB report-body ceiling inherited from the contract,
eight agent steps, 50KB context, and deadline checks around model calls. Do not
scale processes or replicas without shared limits and suitable database storage.
No per-client unauthorized traffic limiter or proxy is supplied in this milestone.

Request logs contain random request ID, HTTP status and duration only. They omit
paths, patient identifiers, body, credential and exception details. Correlate
client `X-Request-ID` with logs; 429/503 responses include Retry-After. On storage
errors, stop writes and follow OPERATIONS.md. Capacity errors can be retried;
do not automatically retry an investigation after an ambiguous network failure
unless you supplied the same Idempotency-Key: the authenticated API now replays a completed saved request for the same reviewer and body. Pending/conflicting requests return 409.

Gunicorn documentation and MIT license checked during implementation:
- https://gunicorn.org/reference/settings/
- https://github.com/benoitc/gunicorn/blob/master/LICENSE

The installed/tested wheel is pinned to 26.2.0 with its SHA-256. This is a tested
runtime increment, not a declaration of production readiness.
