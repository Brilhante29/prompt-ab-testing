# Reuse Delta: prompt-ab-testing

| Candidate | Decision | Reason |
|---|---|---|
| Blinded experiment matrix schema | backlog for kit | Prompt experiments need one stable, provider-neutral evidence boundary. |
| Exact match and token F1 metrics | backlog for shared eval library | RAG, LLM, and prompt projects should not drift on metric definitions. |
| Prompt texts and outputs | repo-local/private mapping | Blinding and project evidence must remain experiment-owned. |

No shared library is extracted until another repository consumes the same contract.
