# Agent Handoff

This file records verifiable state and decisions, not private reasoning.

## Current State

- The producer generated 30 responses with local Ollama `qwen2.5-coder:0.5b`, digest `sha256:4ff64a7...3fb09`, with zero failures.
- Generation source is `be48b03f4c440803f577d3ca0af3494744b56b16`; producer image is `sha256:a451c1d64ff6f69878967474da28ba1e3cb84f95fe62bc4d5e0cebacc7aab32a`.
- Concise variants `v_02` and `v_03` scored `0.80`; explanatory baseline `v_01` scored `0.00`.
- Each concise variant has paired uplift `+0.80`, bootstrap CI `[0.50, 1.00]`, against `v_01`.
- The two leading variants tie. Do not claim one concise prompt is better.

## Contracts

- Generation inputs: `data/fixtures/generation-cases.jsonl`
- Evaluator answers: `data/fixtures/cases.jsonl`
- Prompt mapping: `data/fixtures/prompt-templates.json`
- Blinded IDs: `data/fixtures/variants.json`
- Outputs and provenance: `data/fixtures/outputs.jsonl`, `outputs.provenance.json`
- Raw and V2 results: `benchmarks/results/prompt-ab-baseline.json`, `benchmarks/publication/prompt-ab-baseline-v2.json`

## Continue Safely

1. Keep provider transport outside scoring.
2. Run unit tests and `./tools/validate-project.ps1 -SkipDocker`.
3. Reproduce evaluation with Docker `--network none`.
4. Generate V2 only from a clean source commit and exact image.
5. Require GitHub Actions to pass on the exact `main` SHA.
