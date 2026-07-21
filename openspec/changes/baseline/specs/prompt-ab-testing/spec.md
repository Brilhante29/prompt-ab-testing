# prompt-ab-testing Specification

## ADDED Requirements

### Requirement: blinded experiment

The system SHALL accept only opaque variant IDs with `blinded: true` and SHALL NOT use semantic labels, multipliers, or penalties in scoring.

#### Scenario: blinded variant set

- GIVEN at least two opaque variant IDs
- WHEN the experiment is loaded
- THEN scoring proceeds without prompt names or semantic labels.

### Requirement: deterministic complete evidence

Every case SHALL declare an expected answer and supported deterministic metric, and every variant SHALL supply exactly one output for every case.

#### Scenario: complete output matrix

- GIVEN a complete case and variant matrix
- WHEN evaluation runs
- THEN every output is scored against its expected answer
- AND per-variant means, intervals, sample counts, and raw scores are reported
- AND all tied leaders are preserved.

### Requirement: fail-closed experiment validation

The system SHALL reject unknown IDs, duplicate outputs, unblinded metadata, and incomplete matrices without writing a benchmark result.

#### Scenario: incomplete output matrix

- GIVEN a case and variant pair without an output
- WHEN evaluation runs
- THEN the command exits with a validation error
- AND no partial ranking is accepted.
