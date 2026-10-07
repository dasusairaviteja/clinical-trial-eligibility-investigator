# Offline preparation and research controls

Use only synthetic patient records and public trial records whose terms you have
reviewed. No network fetch or dataset redistribution occurs in these adapters.
The supplied historical archive's redistribution terms remain unresolved.

```sh
python -m clinical_trial.prepare_data trial-candidate local-data/study.json local-data/candidate.json
python -m clinical_trial.prepare_data approve-trial local-data/candidate.json local-data/approved.json --reviewer YOUR_REVIEWER_ID --approved-ids c1 c2
python -m clinical_trial.prepare_data synthetic-source local-data/observation.json local-data/source.json --attest-synthetic
```

Review every extracted criterion before using approve-trial. Unparsed lines block
promotion. Approval outputs contain a version-pinned trial and provenance; an
operator adds that trial to the registry's trials array and validates the registry.
Synthetic-source emits one source object for the sources array. Neither command
silently changes the live registry. Outputs must not already exist.

The project observation schema requires schema=`synthetic-observation-v1`,
patient_id, source_id, version, type and name. Measurement records additionally
require date (ISO date), value (finite decimal string), unit. Event-history records
require events (ISO-date array), complete_since and complete_through (both null or
ordered ISO dates). This is a small project schema, not a FHIR converter.

Recognized rule examples:
- `Measurement hemoglobin gte 9 g/dL on 2026-10-06`
- `Event stroke within 6 months before 2026-10-06`

Operators must approve any transformation of trial language into these explicit
rules. Never infer complete observation coverage from an empty events list.
Multiple matching source assessments abstain. Tests use invented observations,
not clinical validation data.

Official references consulted:
- https://www.nlm.nih.gov/pubs/techbull/ma24/ma24_clinicaltrials_api.html
- https://clinicaltrials.gov/data-api/api
- https://clinicaltrials.gov/about-site/terms-conditions

The dynamic terms page did not expose its full content to the retrieval tool.
No license clearance is claimed and no new public study dataset is committed.
