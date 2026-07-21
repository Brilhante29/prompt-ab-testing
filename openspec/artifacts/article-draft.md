# #10 prompt-ab-testing: 0.9365 from blinded supplied outputs

The old demo multiplied the same answers by variant-specific constants, so its winner was selected before evaluation. The replacement accepts opaque IDs, deterministic expected answers, and one supplied output per case and variant.

The committed fixture reports `v_01` at `0.9365` across four cases with interval `[0.8635, 1.0]`. Exact match and token F1 determine the scores. If outputs change, the leader can change; equal means remain a tie.

The result demonstrates the harness, not general prompt superiority. Generation stays outside the evaluator so local and cloud runners can share the same blinded contract.
