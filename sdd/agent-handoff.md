# Agent Handoff

This file records verifiable state and decisions, not private reasoning.

## Current State

- The evaluator scores complete supplied blinded output matrices with exact match or token F1.
- Baseline apparent leader: `v_01`, mean `0.9365`, bootstrap CI `[0.873, 1.0]`.
- Paired uplift over `v_02`: `0.2222`, CI `[-0.0833, 0.75]`; conclusion is `inconclusive`.
- One process run scores 12 case/variant outputs; `repeat=1` and `measured_iterations=12`.
- Status is `published`; V2 points to source SHA `b7ea2d06bbf520dced03f3671c5ffde9b76647f9`, whose CI run `30860542964` passed every step.

## Contracts

- Variants: `data/fixtures/variants.json`
- Cases: `data/fixtures/cases.jsonl`
- Outputs: `data/fixtures/outputs.jsonl`
- Raw result: `benchmarks/results/prompt-ab-baseline.json`
- Publication config: `benchmarks/config/prompt-ab-baseline-v2.json`
- Publication evidence: `benchmarks/publication/prompt-ab-baseline-v2.json`

## Continue Safely

1. Run `python -m unittest discover -s tests -v`.
2. Run `./tools/validate-project.ps1 -SkipDocker`.
3. Build and execute Docker with `--network none`.
4. Generate V2 only through `tools/generate-publication-benchmark.py` from a clean source commit.
5. Require any new publication commit to pass GitHub Actions on its exact SHA.

Do not add a provider SDK to the evaluator or describe the four-case result as a statistically established prompt winner.