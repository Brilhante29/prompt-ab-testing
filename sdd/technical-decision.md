# Technical Decision

- Runtime: Python CLI packaged through `pyproject.toml`.
- Dependencies: Python standard library for HTTP, validation, metrics, and bootstrap.
- Boundary: the OpenAI-compatible producer emits a provider-neutral file contract; the evaluator imports no provider transport.
- Local-first provider: Ollama; real-cloud replacement: any compatible `/v1/chat/completions` endpoint.
- Inputs: separate generation cases, evaluator answers, prompt templates, blinded IDs, outputs, and provenance.
- Metrics: normalized exact match and multiset token F1.
- Statistics: 10,000 seeded bootstrap resamples for variant means and paired baseline uplifts.
- Decision rule: call a difference conclusive only when its 95% paired interval excludes zero; preserve ties.
- Work accounting: warmup is excluded; measured requests and case/variant scores are both explicit.
- Docker: non-root, digest-pinned Python image; generation uses an explicit network and evaluation runs offline.

This functional-core/imperative-shell split applies SRP and dependency inversion directly: transport can change without changing experiment policy, while deterministic tests replace the HTTP opener and file inputs independently.
