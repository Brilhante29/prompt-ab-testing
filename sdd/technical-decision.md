# Technical Decision

- Runtime: Python CLI packaged through `pyproject.toml`.
- Core dependencies: Python standard library only.
- Validation dependencies: exact lock with `jsonschema` and build backend tooling.
- Inputs: strict JSON/JSONL variant, case, and output contracts.
- Metrics: normalized exact match and multiset token F1.
- Variant uncertainty: exhaustive percentile bootstrap for small samples, seeded bootstrap above 10,000 resamples.
- Comparison: paired bootstrap of the apparent leader minus runner-up on the same cases.
- Decision rule: call the comparison conclusive only when the uplift 95% interval is strictly above zero.
- Tie policy: preserve all IDs matching the highest unrounded mean.
- Work accounting: `repeat` counts process runs; `measured_iterations` counts case/variant scores.
- Output: V1 shared result plus schema-validated V2 publication evidence with Git, Docker, fixture, config, and lock provenance.
- Docker: non-root, digest-pinned Python 3.12.13 image; publication runs without network access.

Prompt execution remains outside this repository. Provider SDKs and credentials belong to output producers that implement the file contract, preserving dependency inversion and deterministic local evaluation.