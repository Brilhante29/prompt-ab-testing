# Change Proposal: honest blinded prompt evaluation

Project: `prompt-ab-testing` (#10)

## Why

The previous implementation applied per-variant multipliers and penalties to the same answers, which encoded the winner before evaluation.

## Scope

- Validate blinded variant IDs, cases, and supplied outputs strictly.
- Score each case with deterministic exact match or token F1.
- Require a complete case/variant matrix.
- Report means, intervals, sample counts, raw scores, and ties.
- Keep prompt generation and provider SDKs out of the evaluator.

## Acceptance Signal

Changing supplied outputs can change the leader, malformed experiments fail, and no semantic label or multiplier affects scoring.
