# Weighted backlog — total 100% (target pace ≈ 1% / day)

| # | Item | Weight |
|---|---|---|
| 1 | Repo scaffolding, .gitignore/.env hygiene, CI green | 3% |
| 2 | Synthetic data pipeline (Synthea, seeded, versioned) | 8% |
| 3 | Trial criteria ingestion (ClinicalTrials.gov API + cache) | 8% |
| 4 | Agent core + patient-history inspector tools | 12% |
| 5 | Temporal reasoning module | 10% |
| 6 | Missing-information / calibrated abstention handling | 10% |
| 7 | Evidence-linked report generator | 8% |
| 8 | Missing-information checklist output | 5% |
| 9 | Baselines (ordinary RAG, RAG + abstention prompt) | 8% |
| 10 | Evaluation harness + metrics (accuracy, false assertions, evidence, abstention, cost) | 10% |
| 11 | Experiments, ablations, analysis, literature review | 8% |
| 12 | Azure ENG/TEST/PROD deployment (deferred — user deploys later) | 5% |
| 13 | Docs, observability, security review, recovery notes | 5% |
| | **Total** | **100%** |

Rules: one coherent increment per day (~1%), pushed ~9 PM Eastern after the
verification checks pass. No fabricated commits, tests, or progress — reported
numbers are measured.
