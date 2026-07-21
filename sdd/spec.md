# Spec: 10 - prompt-ab-testing

## Claim

Score supplied prompt-variant outputs against deterministic expected answers while preserving opaque variant IDs and reporting samples and uncertainty.

## Acceptance Criteria

- Require at least two opaque IDs and `blinded: true`.
- Require exactly one supplied output for every case/variant pair.
- Support normalized exact match and token F1 without fixture multipliers.
- Derive leaders from observed scores and preserve ties.
- Report per-variant means, 95% intervals, sample counts, and raw case scores.
- Emit the shared benchmark contract and run locally or in Docker without credentials.
