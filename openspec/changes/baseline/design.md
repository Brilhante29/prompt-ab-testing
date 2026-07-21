# Change Design: honest blinded prompt evaluation

## Decision

Use a functional scoring core with separate JSON/JSONL adapters for variants, cases, and outputs. Only opaque IDs cross the evaluation boundary.

## Boundaries

- Prompt runners generate outputs and retain the secret ID-to-prompt mapping.
- The evaluator validates a complete blinded matrix.
- Metric functions score expected and observed answers.
- The CLI persists the shared result.

## Principles

SRP separates generation, blinding, validation, and scoring. DIP points runners at a stable output contract. KISS uses deterministic standard-library metrics. Equal evidence remains a tie.

## Rejected

- Variant multipliers, bonuses, or penalties.
- Semantic variant names during scoring.
- Predetermined winner assertions.
- Arbitrary tie breaking.
