# Reuse Improvement Review

Project: `10 - prompt-ab-testing`

## Review Points

- [x] after scaffold
- [x] after architecture decision
- [x] after first working slice
- [x] after benchmark result
- [x] before publication
- [ ] after CI failure, if applicable

## Findings

| Finding | Classification | Kit Area | Action | Status |
|---|---|---|---|---|
| Image, Git blob, fixture, config, lock, and raw-result provenance are common across benchmark repositories. | `patch_now` | `harness`, `skills` | Reuse the generic V2 producer and publication skill proven by prior macro repositories. | done |
| Exact domain metrics and expected values belong in a repository-local gate. | `reject` | `validation` | Keep `tools/validate_publication.py` specific to prompt A/B semantics. | done |
| Python benchmark repositories share a stable Docker, CI, test, and evidence skeleton. | `backlog` | `templates`, `validation` | Promote the skeleton after all six macro repositories confirm its boundaries. | pending |
| Project fixture content must remain local. | `reject` | `templates` | Keep prompt cases and outputs in this repository. | done |

## Patch Now Decisions

- Added the reusable V2 evidence producer for exact execution-derived provenance.
- Added matching Codex and Claude publication skills.
- Reused the validated CI sequence and exact validation lock.

## Backlog Decisions

- Extract a configurable Python publication validator factory only after #30 confirms which checks are generic.

## Rejected Improvements

- Do not move metric expectations, prompt fixtures, or statistical decision policy into the reuse kit.

## Final Gate

- [x] Reusable improvements were patched or recorded.
- [x] Project-specific implementation was not moved into the kit.
- [x] Validation reflects the required reuse-improvement review gate.