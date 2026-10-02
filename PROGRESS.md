# Implementation progress

## Increment 001 — environment foundation (2026-10-01)

Accepted locally: 1 point of the 100-point project (1% cumulative).
Acceptance: ENG/TEST/PROD recognized, invalid configuration rejected without
printing input, credential-free CLI, six tests passing, tracked dotenv guard,
and workflow defining each requested GitHub environment. Remote CI/environment
creation must be confirmed in the PR checks before merge.

No clinical agent, data ingestion, Azure deployment or research results yet.
This is AI-assisted implementation, reviewed and executed by the coding agent.

The existing BACKLOG.md contains a different phase allocation from the approved
conversation plan. Preserve it as prior planning history. Use this allocation
for future acceptance, without double counting: foundation/CI 8 (1 accepted),
data/contracts/ingestion 12, baselines/evaluation 12, agent/tools 18,
temporal/missing-evidence controls 14, reviewer UI/reports 10,
security/reliability/observability 10, deployment/recovery 8, research release 8.
Remaining foundation work: packaging/container setup, richer CI/security checks
and reproducible execution; phase is not complete.

Next increment: define evidence and criterion contracts, preserving exclusion
polarity and explicit unknown semantics. Expert labels and cloud budget remain
open decisions; neither blocks local foundation work.
