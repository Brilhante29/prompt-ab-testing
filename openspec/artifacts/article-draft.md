# #10 prompt-ab-testing: +0.80 from response-format instructions

A pinned local `qwen2.5-coder:0.5b` model generated 30 responses for three blinded prompts. Concise extraction variants scored `0.80`; the explanatory baseline scored `0.00`. Both paired uplifts were `+0.80`, with bootstrap 95% CI `[0.50, 1.00]`.

The result is narrower than “prompt engineering works.” It shows that response-format instructions materially affected exact-answer compliance on ten committed context tasks. The concise prompts tied, and the harness preserves that tie.

The implementation is split at a file contract: an OpenAI-compatible producer records model, image, source, token, latency, and artifact provenance; an offline evaluator sees only opaque variant IDs and deterministic answer metrics. That boundary keeps provider transport replaceable and the scoring core reproducible.
