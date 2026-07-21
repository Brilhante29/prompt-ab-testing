# Architecture Decision

Decision: functional core with separate case, output, and blinded-variant file adapters.

Prompt generation is outside the evaluation boundary. The core validates a complete experiment matrix and scores each supplied answer with the metric declared by its case. Variant IDs are opaque and semantic names are rejected by contract.

This applies SRP and DIP where they matter: runners produce evidence, metrics score evidence, and the CLI persists results. It also keeps the local-first path independent from provider credentials.

Rejected:

- Fixture multipliers or penalties: they encode the winner before evaluation.
- Variant names in results: they weaken blinding.
- Arbitrary tie breaking: equal evidence must remain a tie.
- Provider SDK in the evaluator: generation and evaluation have different responsibilities.
