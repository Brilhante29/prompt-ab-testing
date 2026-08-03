# Release Checklist

- [x] README opens with project number and measured result.
- [x] Blindness, matrix completeness, paired uplift, and tie behavior have regression tests.
- [x] `repeat` and measured workload size are not conflated.
- [x] Docker image is version-and-digest pinned and runs offline as non-root.
- [x] Validation dependencies and Python build backend are exactly pinned.
- [x] Reuse improvement review is complete.
- [x] V2 evidence was generated from source commit `b7ea2d06bbf520dced03f3671c5ffde9b76647f9`.
- [x] Source gate passed GitHub Actions run `30860542964`; the publication commit must pass again on its exact SHA.

Status is `published` with committed V2 evidence; exact-head publication CI is recorded centrally after the push.