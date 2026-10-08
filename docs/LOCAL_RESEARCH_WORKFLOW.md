# Local research workflow

Azure access, environment configuration and secrets are deferred at the user's
request. These commands run locally without model credentials. Use synthetic
patients only. AI-assisted implementation is not a substitute for clinical review.

## Public trial snapshot

```sh
python -m clinical_trial.trial_fetch NCT02993146 local-data/my-trial-snapshot
```

The fetcher sends only the NCT identifier to the fixed ClinicalTrials.gov API.
It rejects redirects, wrong identifiers, non-JSON responses, duplicate keys and
responses over 1 MB. It records a retrieval time and exact downloaded-byte hash.
It performs one request without automatic retries or refresh. Existing snapshots
are never overwritten. `local-data/` is ignored by git; do not move raw records
into tracked directories. An older snapshot is not evidence of current recruitment.

The snapshot contains raw data and a review candidate. It does not enter the
trusted registry automatically. Review inclusion/exclusion polarity, multiline
criteria and parser issues, then use the existing approval workflow in
DATA_PREPARATION.md. Do not assume trial language matches the executable grammar.

API documentation was checked via NLM's official API announcement and example:
https://www.nlm.nih.gov/pubs/techbull/ma24/ma24_clinicaltrials_api.html
https://sites.wip.nlm.nih.gov/pubs/techbull/ja25/ja25_clinical_trials_screen-scraping.html
Source terms: https://clinicaltrials.gov/about-site/terms-conditions
The terms page did not expose its substantive text through the reader used here.
Redistribution licensing is therefore unverified. The user-provided ZIP archive
is also not cleared for redistribution. No raw public snapshot is included in git.

## Explicit rule grammar

In addition to dated measurements, age thresholds and calendar-month windows:

```text
Event stroke within 30 days before 2026-10-08
All of: ["Age at least 18 years on 2026-10-08", "Measurement hemoglobin gte 9 g/dL on 2026-10-08"]
Any of: ["Age under 18 years", "Age over 65 years"]
```

Day windows use inclusive calendar dates and elapsed-day subtraction. Month
windows retain calendar-month semantics; they are not converted into 30-day units.
Absent events need complete coverage of the entire window. Compound rules accept
2–8 explicit, non-nested clauses. All-of is contradicted by a contradicted clause;
any-of is supported by a supported clause. Otherwise unknown propagates unless
every required clause is decisive. Citations come from the decisive children.
Trial inclusion/exclusion polarity is applied by the report contract afterward.
Undated age remains a demonstration feature, not a temporally aligned assessment.

## Frozen cohort and blinded review

Create a JSON array of trusted requests with the same fields as the workspace's
advanced request editor. Remove `schema_version` and authored `findings` from
legacy case examples. Keep patient/trial-disjoint partitioning outside the runner
and freeze it before experimentation using `dataset.split_components`.

```sh
python -m clinical_trial.cohort examples/synthetic_sources.json local-data/requests.json local-data/cohort.json
python -m clinical_trial.adjudication prepare local-data/cohort.json local-data/review.json local-data/private-key.json
```

The default arm is rules-only. The batch runner preflights every reference before
running any planner, rejects duplicate patient/trial/criterion identities and
preserves all case outputs. Paid arms remain opt-in and are deferred. Byte/call
ceilings are common across arms, but actual token consumption is not matched.

Give reviewers `review.json` plus secure read access to the full source registry,
trial snapshots and frozen labeling protocol. Cited excerpts alone are insufficient
for deciding that evidence is missing. Keep `private-key.json` away from reviewers:
it maps the shuffled review IDs to arms. IDs are pseudonymous, not anonymized or
cryptographically secret. Ask independent reviewers to fill `gold`,
`evidence_correct`, `reviewer` and `rationale`; do not edit criterion content.
Adjudicate disagreements against the same source documents before scoring.

```sh
python -m clinical_trial.adjudication score local-data/cohort.json local-data/review.json local-data/private-key.json --output local-data/metrics.json
```

Scoring rejects incomplete/duplicate reviews, changed cohorts or evidence, and
inconsistent gold labels across arms. It does not certify reviewer qualifications.
Unmeasured model cost remains null; total cost is null if any prediction is
unpriced. Case-level latency/cost are allocated evenly to criterion rows, while
the original case totals remain in `runs`; this is not per-criterion timing.

## Manual acceptance still required

Use the authenticated workspace to complete the following sessions with actual
reviewers and record browser/assistive technology, observer, date, issues and
remediation. None of these sessions is claimed to have occurred:

1. Keyboard-only connect, investigate, inspect evidence, correct and export.
2. Screen-reader heading, label, status-update and correction-history navigation.
3. Magnification/zoom and narrow-screen review of long quotes and long IDs.
4. Two reviewers correcting the same revision and recovering from a conflict.
5. Recovery from network failure/disconnect without duplicate investigation.
6. Clinician interpretation of supported/contradicted/unknown under both polarities.

Independent security review must cover credential handling, shared-workspace
authorization, injection boundaries, audit tampering, recovery, dependency risks
and deployment-representative load. Existing automated checks do not replace it.
