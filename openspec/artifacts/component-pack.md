# Component Pack: prompt-ab-testing

## Selected Pack

- Pack id: `ai-evaluation-retrieval`
- Pack name: AI Evaluation and Retrieval Systems
- Problem: Evaluate LLM, RAG, embeddings, prompts, agents, and inference cost with reproducible evidence.

## Benchmark Focus

- exact_match
- f1
- recall_at_k
- latency_ms
- cost_per_query_usd
- task_success_rate

## Preferred Artifacts

- evaluation fixtures
- answer/reference pairs
- retrieval corpus
- deterministic local runner
- cost table

## Rejection Rules

- Reject demos that require paid model credentials for the default path.
- Reject quality claims without benchmark JSON.
- Reject hidden prompts without prompt/version attribution.

## Reuse Priority

1. Use repo-local `.codex/skills/` and `.claude/skills/`.
2. Use `.portfolio/` and upstream `portfolio-reuse-kit`.
3. Use external repositories as references for organization, workflow, schemas, tests, benchmarks, and docs.
4. Use external code only with license compatibility, attribution, and a decision record.
