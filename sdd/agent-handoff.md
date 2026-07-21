# Agent Handoff

Project: `10 - prompt-ab-testing`

## Current State

- Fixture multipliers, semantic variant names, and predetermined winner assertions were removed.
- The repository scores supplied blinded outputs with exact match or token F1.
- Baseline: `v_01` mean `0.9365` across four cases, interval `[0.8635, 1.0]`.
- Status is `benchmarked`; publication and remote CI evidence are not claimed.

## Contracts

- Variants: `data/fixtures/variants.json`
- Cases: `data/fixtures/cases.jsonl`
- Outputs: `data/fixtures/outputs.jsonl`
- Shared result: `benchmarks/results/prompt-ab-baseline.json`

## Continue Safely

1. Run `$env:PYTHONPATH='src'; python -m unittest discover -s tests -v`.
2. Run the benchmark command from `project.yaml`.
3. Run `./tools/validate-project.ps1 -SkipDocker`, then the Docker validation.
4. Inspect `git diff --check` and confirm README numbers match the JSON.
5. Do not reveal semantic prompt labels until scoring is frozen.
6. Do not change status to `published` without remote/upstream and green CI evidence.

No code task is intentionally left half-finished. The next meaningful extension is a separate local/provider runner that exports the same blinded output contract.
