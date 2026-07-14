# Architecture Decision

Decision: Clean, CLI-first benchmark application.

Rationale: the project proves evaluation behavior, so metrics and orchestration are kept in pure Python modules.
CLI, Docker, and future provider adapters depend inward.

Rejected:

- External managed service as default path: would make the baseline non-reproducible.
- Web UI first: would distract from the benchmark evidence.
- Broker/event-driven flow: no async workload is required for the baseline.
