# Benchmark Plan

Primary metric: `highest_mean_score`.

```powershell
python -m prompt_ab_testing benchmark --cases data/fixtures/cases.jsonl --outputs data/fixtures/outputs.jsonl --variants data/fixtures/variants.json --output benchmarks/results/prompt-ab-baseline.json
```

Each case declares normalized exact match or token F1. Every blinded variant receives one score per case. The result reports mean, sample-wise normal-approximation 95% interval, sample count, and raw scores. The committed four-case fixture demonstrates reproducibility; it is too small to establish statistical superiority.
