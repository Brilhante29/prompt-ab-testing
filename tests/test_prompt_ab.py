import json
import tempfile
import unittest
from pathlib import Path

from prompt_ab_testing.cli import (
    ExperimentValidationError,
    evaluate,
    exact_match,
    token_f1,
)


class PromptABTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def write_json(self, name, value):
        path = Path(self.temp_dir.name, name)
        path.write_text(json.dumps(value) + "\n", encoding="utf-8")
        return path

    def write_jsonl(self, name, records):
        path = Path(self.temp_dir.name, name)
        path.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )
        return path

    def test_scores_deterministic_task_metrics(self):
        self.assertEqual(exact_match("Local-first", "local first"), 1.0)
        self.assertEqual(exact_match("yes", "yes indeed"), 0.0)
        self.assertAlmostEqual(token_f1("a b c", "a b"), 0.8)

    def test_evaluates_only_supplied_blinded_outputs(self):
        result = evaluate()

        self.assertTrue(result["blinded"])
        self.assertEqual(result["summary"]["case_count"], 4)
        self.assertEqual(result["summary"]["variant_count"], 3)
        self.assertEqual(result["leading_variant_ids"], ["v_01"])
        self.assertEqual(result["repeat"], 1)
        self.assertEqual(result["measured_iterations"], 12)
        self.assertNotIn("name", result["variants"][0])
        self.assertNotIn("multiplier", json.dumps(result))
        leader = result["variants"][0]
        self.assertEqual(leader["sample_count"], 4)
        self.assertEqual(leader["ci95_lower"], 0.873)
        self.assertEqual(leader["ci95_upper"], 1.0)
        self.assertEqual(leader["ci95_method"], "exhaustive-bootstrap")
        self.assertEqual(leader["bootstrap_resamples"], 256)

        comparison = result["paired_comparison"]
        self.assertEqual(comparison["leader_variant_id"], "v_01")
        self.assertEqual(comparison["runner_up_variant_id"], "v_02")
        self.assertEqual(comparison["mean_uplift"], 0.2222)
        self.assertEqual(comparison["uplift_ci95_lower"], -0.0833)
        self.assertEqual(comparison["uplift_ci95_upper"], 0.75)
        self.assertFalse(comparison["conclusive"])

    def test_emits_shared_contract_and_uncertainty(self):
        result = evaluate()
        required = {"project", "metric", "value", "unit", "timestamp", "command"}
        self.assertTrue(required.issubset(result))
        self.assertEqual(result["metric"], "highest_mean_score")
        for variant in result["variants"]:
            self.assertLessEqual(variant["ci95_lower"], variant["mean_score"])
            self.assertGreaterEqual(variant["ci95_upper"], variant["mean_score"])
            self.assertEqual(len(variant["scores"]), variant["sample_count"])

    def test_result_changes_when_supplied_outputs_change(self):
        cases = self.write_jsonl(
            "cases.jsonl",
            [{"id": "c", "metric": "exact_match", "expected": "right"}],
        )
        variants = self.write_json(
            "variants.json", {"blinded": True, "variant_ids": ["v_01", "v_02"]}
        )
        outputs = self.write_jsonl(
            "outputs.jsonl",
            [
                {"case_id": "c", "variant_id": "v_01", "output": "wrong"},
                {"case_id": "c", "variant_id": "v_02", "output": "right"},
            ],
        )

        result = evaluate(cases, outputs, variants)

        self.assertEqual(result["leading_variant_ids"], ["v_02"])
        self.assertEqual(result["value"], 1.0)
        self.assertEqual(result["repeat"], 1)
        self.assertEqual(result["measured_iterations"], 2)
        comparison = result["paired_comparison"]
        self.assertEqual(comparison["mean_uplift"], 1.0)
        self.assertEqual(comparison["uplift_ci95_lower"], 1.0)
        self.assertEqual(comparison["uplift_ci95_upper"], 1.0)
        self.assertEqual(comparison["bootstrap_resamples"], 1)
        self.assertTrue(comparison["conclusive"])

    def test_preserves_ties_without_claiming_a_pairwise_winner(self):
        cases = self.write_jsonl(
            "cases.jsonl",
            [{"id": "c", "metric": "exact_match", "expected": "right"}],
        )
        variants = self.write_json(
            "variants.json", {"blinded": True, "variant_ids": ["v_01", "v_02"]}
        )
        outputs = self.write_jsonl(
            "outputs.jsonl",
            [
                {"case_id": "c", "variant_id": "v_01", "output": "right"},
                {"case_id": "c", "variant_id": "v_02", "output": "right"},
            ],
        )

        result = evaluate(cases, outputs, variants)

        self.assertEqual(result["leading_variant_ids"], ["v_01", "v_02"])
        self.assertEqual(result["paired_comparison"]["ci95_method"], "tie")
        self.assertFalse(result["paired_comparison"]["conclusive"])
    def test_rejects_unblinded_or_incomplete_experiments(self):
        cases = self.write_jsonl(
            "cases.jsonl",
            [{"id": "c", "metric": "exact_match", "expected": "right"}],
        )
        variants = self.write_json(
            "variants.json", {"blinded": False, "variant_ids": ["v_01", "v_02"]}
        )
        outputs = self.write_jsonl(
            "outputs.jsonl",
            [{"case_id": "c", "variant_id": "v_01", "output": "right"}],
        )
        with self.assertRaisesRegex(ExperimentValidationError, "blinded"):
            evaluate(cases, outputs, variants)

        variants = self.write_json(
            "variants-valid.json",
            {"blinded": True, "variant_ids": ["v_01", "v_02"]},
        )
        with self.assertRaisesRegex(ExperimentValidationError, "incomplete"):
            evaluate(cases, outputs, variants)


if __name__ == "__main__":
    unittest.main()
