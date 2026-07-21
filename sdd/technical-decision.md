# Technical Decision

- Runtime: Python CLI packaged through `pyproject.toml`.
- Dependencies: standard library only.
- Inputs: strict JSON/JSONL variant, case, and output contracts.
- Metrics: normalized exact match and multiset token F1.
- Uncertainty: 95% normal approximation over case scores, clipped to `[0, 1]`.
- Tie policy: return every ID matching the highest rounded mean.
- Output: shared portfolio benchmark JSON with timestamp, command, samples, summary, and environment.
- Docker: installs the local package and runs the same benchmark command.

Prompt/provider execution stays outside the repository; it only needs to export the output matrix.
