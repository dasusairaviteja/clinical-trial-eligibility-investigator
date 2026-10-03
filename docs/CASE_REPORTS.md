# Case-to-report boundary, schema version 1

Run the wholly authored, synthetic example from the repository root:

```bash
python -m clinical_trial.report examples/synthetic_case.json
```

The command validates existing findings; it does not generate findings or call
a model. Valid input produces JSON on stdout with `human_review_required` status.
Invalid input produces a generic stderr message and exit code 2, without a
partial report or source text in errors. Successful reports intentionally include
cited quotes and clarification questions: treat their output as sensitive.

The example defines every required field. All objects reject extra/missing keys;
arrays must be arrays, not null; enum values are lowercase strings. Version is
integer 1, not true or 1.0. UTF-8 input is capped at 1,000,000 bytes, each array at
500 items; repeated keys, NaN and Infinity are rejected. Empty criteria, duplicate
criterion IDs, missing/extra findings, foreign-trial criteria and foreign-patient
sources are errors. Existing evidence contracts validate citations against exact
source snapshots. Criteria order controls output order; no wall-clock metadata
is injected, allowing reproducible output. Whole source documents are omitted.

This schema is separate from the current browser demo export. Do not assume UI
JSON passes validation: an explicit adapter and trusted server-side source lookup
are still required. Input case identity is not authentication; uploaded source
text is not independently verified. Quote matching does not establish clinical
truth or temporal relevance. No patient-level eligibility conclusion is emitted.

Uses the Python standard library only. JSON behavior checked against:
https://docs.python.org/3.12/library/json.html
