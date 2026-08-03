# #10 prompt-ab-testing: 0.9365 without a false winner claim

The original demo multiplied identical answers by variant-specific constants, selecting a winner before evaluation. The replacement accepts opaque IDs, deterministic expected answers, and exactly one supplied output per case and variant.

The committed fixture gives `v_01` an apparent mean lead at `0.9365`. Its paired uplift over `v_02` is `0.2222`, but the exhaustive-bootstrap 95% interval is `[-0.0833, 0.75]`. Because that interval includes zero, the result is inconclusive.

This is the useful result: the harness can reject unblinded or incomplete experiments, derive rankings from evidence, preserve ties, and refuse an unsupported superiority claim. Prompt generation remains a separate adapter, so local and cloud runners can share the same output contract.