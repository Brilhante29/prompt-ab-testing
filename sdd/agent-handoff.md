# Agent Handoff

Project: `10 - prompt-ab-testing`

## Roles

- principal-agent: coordinates implementation, validation, and publication.
- benchmark-harness-agent: verifies metric and result JSON.
- reuse-improvement-reviewer: records whether the portfolio kit should improve.

## Gates

- Local benchmark passes.
- Docker build passes.
- `tools/validate-project.ps1` passes.
- Reuse improvement final gate is complete.
