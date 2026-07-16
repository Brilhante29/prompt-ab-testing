# Architecture Record: prompt-ab-testing

## Decision

- Architecture: `clean-architecture`
- Stack profile: `python`
- API style: `cli-first`
- Messaging: `none`
- Database/runtime: `fixture-files` / `python-cli`

## Reason

The metric and benchmark use cases must stay independent from CLI, fixtures, and future providers.

## Dependency Direction

Domain metrics and application benchmark orchestration do not import interface code.

## Boundaries

- none recorded

## Library Policy

Prefer standard library for baseline reproducibility; add provider libraries only behind adapters.

## Principle Check

- SRP: keep benchmark, API, use cases, and adapters separate.
- OCP: new providers must be adapters, not domain rewrites.
- LSP: replacement providers must preserve observable behavior.
- ISP: ports stay narrow.
- DIP: application depends on behavior, not infrastructure.
- KISS/YAGNI: leave out anything that does not improve the benchmark.
