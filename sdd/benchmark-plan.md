# Benchmark Plan

## Command

```powershell
python -m prompt_ab_testing benchmark --cases data/fixtures/cases.jsonl --outputs data/fixtures/outputs.jsonl --variants data/fixtures/variants.json --output benchmarks/results/prompt-ab-baseline.json
```

## Workload

Four cases are scored for three blinded variants, producing 12 measured output scores in one process run. Each case declares normalized exact match or token F1. Every variant must supply exactly one output per case.

## Statistics

Each variant receives a mean and a 95% percentile interval. With four cases, all `4^4 = 256` bootstrap resamples are enumerated. The apparent leader is compared with the runner-up through paired per-case differences using the same exhaustive bootstrap.

A comparison is conclusive only when the uplift interval is strictly above zero. The baseline uplift is `0.2222` with CI `[-0.0833, 0.75]`, so no winner claim is permitted.

## Publication

The V1 result records metric samples and workload counts. The V2 producer binds that result to the source commit, exact Docker image digest, committed fixture tree, benchmark config, and validation lock. Docker execution uses `--network none`.