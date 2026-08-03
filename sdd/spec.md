# Spec: 10 - prompt-ab-testing

## Claim

Evaluate supplied blinded prompt outputs with deterministic task metrics and paired uncertainty, without embedding a prompt runner or predetermined winner.

## Acceptance Criteria

- Require at least two opaque IDs and `blinded: true`.
- Require exactly one supplied output for every case/variant pair.
- Support normalized exact match and token F1 without fixture multipliers.
- Derive leaders from unrounded observed means and preserve ties.
- Report per-variant means, bootstrap 95% intervals, sample counts, and raw case scores.
- Compare a unique apparent leader with the runner-up using paired bootstrap differences.
- Mark the comparison inconclusive whenever the uplift interval includes zero.
- Keep process repetitions separate from measured case/variant evaluations.
- Emit V1 and provenance-bound V2 benchmark contracts.
- Run locally and in non-root, network-disabled Docker without credentials.