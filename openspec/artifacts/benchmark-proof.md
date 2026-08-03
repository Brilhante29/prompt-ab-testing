# Benchmark Proof: prompt-ab-testing

- Metric: `highest_mean_score`
- Value: `0.9365`
- Apparent leader: `v_01`
- Leader bootstrap CI: `[0.873, 1.0]`
- Paired uplift over `v_02`: `0.2222`
- Paired uplift CI: `[-0.0833, 0.75]`
- Conclusion: `inconclusive`
- Cases: `4`
- Variants: `3`
- Measured outputs: `12`
- Process runs: `1`
- Raw result: `benchmarks/results/prompt-ab-baseline.json`
- Publication evidence: `benchmarks/publication/prompt-ab-baseline-v2.json`

```powershell
python -m prompt_ab_testing benchmark --cases data/fixtures/cases.jsonl --outputs data/fixtures/outputs.jsonl --variants data/fixtures/variants.json --output benchmarks/results/prompt-ab-baseline.json
```

All `256` small-sample bootstrap resamples are enumerated. Because the paired uplift interval includes zero, this evidence demonstrates the evaluation harness but does not establish a superior prompt.