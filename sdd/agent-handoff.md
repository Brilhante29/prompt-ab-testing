# Agent Handoff

This file records verifiable state and decisions, not private reasoning.

## Current State

- The evaluator scores complete supplied blinded output matrices with exact match or token F1.
- Baseline apparent leader: `v_01`, mean `0.9365`, bootstrap CI `[0.873, 1.0]`.
- Paired uplift over `v_02`: `0.2222`, CI `[-0.0833, 0.75]`; conclusion is `inconclusive`.
- One process run scores 12 case/variant outputs; `repeat=1` and `measured_iterations=12`.
- Source publication gates are implemented; final V2 evidence and remote CI are pending.

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
4. Commit a clean source tree before generating V2 evidence.
5. Generate V2 only through `tools/generate-publication-benchmark.py`.
6. Publish only after the exact pushed commit has green remote CI.

Do not add a provider SDK to the evaluator or describe the four-case result as a statistically established prompt winner.