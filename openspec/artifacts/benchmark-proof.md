# Benchmark Proof: prompt-ab-testing

- Model: `qwen2.5-coder:0.5b`, digest `sha256:4ff64a7...3fb09`
- Metric: `highest_mean_score`
- Highest value: `0.80`
- Leading variants: `v_02`, `v_03` (tie)
- Baseline `v_01`: `0.00`
- Paired uplift versus baseline: `+0.80`
- Paired uplift CI95: `[0.50, 1.00]`
- Cases / variants / measured responses: `10 / 3 / 30`
- Generation failures: `0`
- Generation p95: `941.55 ms`

The evidence demonstrates exact-answer compliance on this bounded workload. It does not establish general model quality or superiority between the tied concise prompts.
