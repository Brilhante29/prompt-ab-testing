# Verification: prompt-ab-testing

## Completed Locally

- Eight unit tests cover scoring, ties, matrix completeness, fake HTTP generation, and template mismatch.
- A pinned local model generated 30 responses after one excluded warmup with zero failures.
- Output provenance binds model, producer source/image, artifact inputs, token counts, and latency.
- Evaluation preserves the tied leaders while separately reporting paired uplift against baseline.
- Docker evaluation runs offline as a non-root user.
- V2 schema and Git-bound provenance validation are required before publication.

## Boundary

Ten hand-authored context cases are a portfolio benchmark, not a general prompt-quality study. The measured result supports only the exact-answer formatting claim on the committed workload and model.
