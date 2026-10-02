# Evidence contracts — increment 002

`clinical_trial.contracts` uses frozen Python dataclasses and explicit runtime
validation, without external dependencies. It is not connected to the UI yet.

- Criterion: local ID, trial ID, original statement, inclusion/exclusion kind.
- SourceDocument: source ID, patient ID, version, exact source text snapshot.
- Citation: source ID/version, start/end Unicode character offsets, exact quote.
- Finding: criterion ID, supported/contradicted/unknown, immutable citations,
  and missing-information questions.

`validate_finding` rejects mismatched criterion IDs, foreign-patient evidence,
ambiguous source IDs, stale source versions, and quotes that do not match their
specified span. Definitive findings need citations; unknown findings need at
least one clarification question. Raw text is omitted from object representations
and error messages, but this is not a substitute for secure logging controls.

| Criterion kind | Supported | Contradicted | Unknown |
|---|---|---|---|
| Inclusion | No barrier on this criterion | Potential barrier | Needs clarification |
| Exclusion | Potential barrier | No barrier on this criterion | Needs clarification |

No return value means “patient is eligible.” Exact quotation proves provenance,
not semantic entailment, source completeness, temporal validity, or clinical
correctness. The caller must supply trusted patient context and source snapshots;
this validator is not an authorization boundary. Cross-trial/case report assembly
and JSON deserialization are future increments. Offsets are Python Unicode code
points, NOT JavaScript UTF-16 positions; adapters must convert explicitly.

Run: `python -m unittest discover -s tests -v`.

Implementation reference checked: https://docs.python.org/3.12/library/dataclasses.html
