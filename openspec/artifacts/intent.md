# Intent: prompt-ab-testing

## Measurable Claim

Prompt A/B testing harness that scores variants, ranks winners, and reports a reproducible confidence interval.

## Problem

Turns prompt choices into measurable experiments inside the AI Evaluation and RAG Platform.

## In Scope

- Use the selected component pack: `ai-evaluation-retrieval`.
- Keep the project under the AI Evaluation and Retrieval Systems program.
- Preserve the benchmark contract: `best_variant_score` in `benchmarks/results/prompt-ab-baseline.json`.
- Keep the default path local-first and reproducible.

## Out Of Scope

- Paid credentials for the default demo.
- External infrastructure that is not required by the benchmark.
- Replacing local portfolio skills with external components silently.

## Default Demo Path

- Status: benchmarked
- Runtime: python-cli
- Benchmark command: `python -m prompt_ab_testing benchmark --output benchmarks/results/prompt-ab-baseline.json`

## Public Proof

- Benchmark: best_variant_score = 1.00
- Result path: `benchmarks/results/prompt-ab-baseline.json`
