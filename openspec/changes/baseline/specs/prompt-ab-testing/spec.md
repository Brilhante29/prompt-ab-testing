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
- AND per-variant means, bootstrap intervals, sample counts, and raw scores are reported
- AND all tied leaders are preserved.

### Requirement: paired uncertainty

A unique apparent leader SHALL be compared with the runner-up using paired per-case score differences, and SHALL be conclusive only when the 95% uplift interval is strictly above zero.

#### Scenario: interval includes zero

- GIVEN an apparent leader whose paired uplift interval includes zero
- WHEN the result is emitted
- THEN `conclusive` is false
- AND no general superiority claim is made.

Every non-baseline variant SHALL also be compared with the first declared variant through paired per-case differences, including when leaders tie.

#### Scenario: tied leaders beat baseline

- GIVEN two variants tied for the highest mean
- WHEN both paired intervals against baseline exclude zero
- THEN both baseline comparisons are reported as conclusive
- AND the tied leaders remain tied.

### Requirement: explicit work accounting

The result SHALL distinguish process repetitions from measured case/variant evaluations.

#### Scenario: one ten-case three-variant run

- GIVEN ten cases and three variants evaluated once
- WHEN the result is emitted
- THEN `repeat` is `1`
- AND `measured_iterations` is `30`.

### Requirement: replaceable generation adapter

The system SHALL generate outputs through an OpenAI-compatible port and SHALL record model, producer, token, latency, failure, and artifact provenance without coupling scoring to transport.

#### Scenario: local provider generation

- GIVEN a pinned Ollama model behind the compatible endpoint
- WHEN generation completes
- THEN every blinded case/variant output is written
- AND the evaluator can consume the files offline.

### Requirement: fail-closed experiment validation

The system SHALL reject unknown IDs, duplicate outputs, unblinded metadata, and incomplete matrices without writing a benchmark result.

#### Scenario: incomplete output matrix

- GIVEN a case and variant pair without an output
- WHEN evaluation runs
- THEN the command exits with a validation error
- AND no partial ranking is accepted.
