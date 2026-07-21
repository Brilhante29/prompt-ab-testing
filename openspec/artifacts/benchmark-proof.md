# Benchmark Proof: prompt-ab-testing

- Metric: `highest_mean_score`
- Value: `0.9365`
- Leading blinded ID: `v_01`
- Leader interval: `[0.8635, 1.0]`
- Cases per variant: `4`
- Variants: `3`
- Result: `benchmarks/results/prompt-ab-baseline.json`

Command:

```powershell
python -m prompt_ab_testing benchmark --cases data/fixtures/cases.jsonl --outputs data/fixtures/outputs.jsonl --variants data/fixtures/variants.json --output benchmarks/results/prompt-ab-baseline.json
```

The interval is a normal approximation over four case scores. It is uncertainty reporting for the fixture, not a significance claim.
