# Portfolio Impact: prompt-ab-testing

This repository contributes a provider-neutral blinded evaluation contract to AI Evaluation and Retrieval Systems. Local or cloud prompt runners can produce the same matrix without entering the scoring core.

Portfolio proof: a pinned local LLM produced 30 real responses with zero failures. Concise prompts scored `0.80` versus `0.00` for an explanatory baseline, paired uplift `+0.80` with CI `[0.50, 1.00]`. The concise variants tied, demonstrating both measurable prompt effects and an honest no-winner result. V2 evidence binds evaluation to source, Docker image, fixtures, config, and dependency lock.
