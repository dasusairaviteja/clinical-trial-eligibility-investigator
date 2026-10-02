# TREC 2022 Clinical Trials data

Supplementary benchmark data (see EVALUATION.md).

- `topics2022.xml` — 50 patient case topics, NIST TREC 2022 Clinical Trials track.
- `qrels2022.txt` — 35,394 trial-level relevance judgments. NOT committed
  (666 KB, exceeds this machine's push transport limits); fetch with
  `./scripts/fetch_trec2022.sh`, which downloads both files from NIST.
- Full trial corpus: Kaggle `skylord/all-clinical-trials` (488 MB zip, 103,509
  trial XML files in registry native format with eligibility criteria text;
  snapshot dated May 2020; license: Open Database, contents © original authors).
  NOT committed — exceeds GitHub's 100 MB per-file limit (also matched by
  `*.zip` in .gitignore). Ingest with `scripts/import_trials.py`.
  Local copy: `~/workspace/datasets/trec2022/all-clinical-trials-skylord.zip`.

Caveat: the corpus snapshot is stale (May 2020). Use for benchmark comparisons
only; the live ClinicalTrials.gov API remains the source for current criteria.
