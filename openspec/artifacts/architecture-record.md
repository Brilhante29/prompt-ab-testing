# Architecture Record: prompt-ab-testing

- Style: functional core, imperative CLI shell.
- Input adapters: blinded variant JSON plus case and output JSONL.
- Core policies: strict matrix validation, normalized exact match, multiset token F1, mean and 95% interval, tie preservation.
- Output adapter: shared benchmark JSON.
- Dependency rule: no prompt runner, provider SDK, cloud SDK, or variant semantics enter scoring.

The runner/evaluator split lets local and cloud generators produce the same blinded evidence contract.
