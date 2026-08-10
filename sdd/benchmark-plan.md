# Benchmark Plan

## Workload

Ten context-grounded extraction cases are sent to three blinded prompt variants through a pinned `qwen2.5-coder:0.5b` Ollama model. One warmup is excluded; 30 responses are measured and generation must report zero failures.

Expected answers live in a separate evaluator-only file. This prevents the generation prompt from receiving its answer through the benchmark harness.

## Statistics

Each variant receives exact-answer scores, a mean, and a 95% percentile interval from 10,000 seeded bootstrap resamples. Every challenger is also compared with baseline `v_01` through paired per-case score differences. A difference is conclusive only when its interval excludes zero.

Measured concise variants scored `0.80`; explanatory baseline `v_01` scored `0.00`. Both paired uplifts are `+0.80`, CI `[0.50, 1.00]`. The concise variants tied and are not ranked against each other.

## Publication

The producer records model and image digests, source commit, tokens, latency, failure count, and input/output hashes. The V2 publication wrapper additionally binds the evaluated result to the clean source commit, exact Docker image, committed fixture tree, config, and validation lock. Evaluation runs offline with `--network none`.
