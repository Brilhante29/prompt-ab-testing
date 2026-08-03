# Release Checklist

- [x] README opens with project number and measured result.
- [x] Blindness, matrix completeness, and paired uncertainty have regression tests.
- [x] `repeat` and measured workload size are not conflated.
- [x] Docker image is version-and-digest pinned and runs as non-root.
- [x] Publication producer, config, schema, lock, and validator exist.
- [ ] Clean source commit is pushed and its CI is green.
- [ ] V2 evidence is generated from that exact source commit and Docker image.
- [ ] Final publication commit is pushed and its CI is green.