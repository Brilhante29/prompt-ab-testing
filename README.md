# #10 prompt-ab-testing

**Status:** scaffold

**Proves:** comparacao estatistica de prompts.

**Benchmark target:** score_by_variant, confidence_interval.

**Stack:** python, typer, duckdb, scipy, docker.

## Next milestone

Implement the smallest Docker-runnable version and produce the first JSON benchmark under enchmarks/results/.

## Run

`ash
docker build -t prompt-ab-testing .
docker run --rm prompt-ab-testing
`

## Benchmark

`ash
docker run --rm prompt-ab-testing benchmark
`

| Metric | Value | Unit |
|---|---:|---|
| score_by_variant, confidence_interval | pending | pending |

## Architecture

Defined in sdd/spec.md before implementation.

## References

See REFERENCES.md.