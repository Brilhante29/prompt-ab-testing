# Technical Decision

- Runtime: Python CLI packaged through `pyproject.toml`.
- Dependencies: standard library for baseline reproducibility.
- Fixtures: checked into `data/fixtures/`.
- Benchmark: writes JSON to `benchmarks/results/prompt-ab-baseline.json`.
- Docker: installs the local package and runs the benchmark command by default.
