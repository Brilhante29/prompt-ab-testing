# Spec: 10 - prompt-ab-testing

## Claim

Prompt A/B testing harness that scores variants, ranks winners, and reports a reproducible confidence interval.

## Acceptance Criteria

- Runs locally with `python -m prompt_ab_testing benchmark --output benchmarks/results/prompt-ab-baseline.json`.
- Runs in Docker with no paid secret.
- Writes benchmark JSON under `benchmarks/results/`.
- Keeps domain/evaluation logic independent from CLI and future providers.
