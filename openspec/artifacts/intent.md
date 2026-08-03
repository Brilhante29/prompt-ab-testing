# Intent: prompt-ab-testing

Compare supplied prompt outputs without encoding a winner.

- Primary metric: `highest_mean_score`.
- Evidence: per-variant scores, means, intervals, and sample counts.
- Default path: local JSON/JSONL and Python CLI.
- Status: `published` with provenance-bound V2 evidence.
- Excluded: prompt generation, provider credentials, and semantic prompt labels during scoring.
