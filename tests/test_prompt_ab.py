import json
import tempfile
import unittest
from pathlib import Path
from urllib.request import Request

from prompt_ab_testing.cli import (
    ExperimentValidationError,
    evaluate,
    exact_match,
    token_f1,
)
from prompt_ab_testing.producer import (
    GenerationValidationError,
    OpenAICompatibleGenerator,
    generate_output_matrix,
)


class FakeResponse:
    def __init__(self, document):
        self.document = document

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.document).encode("utf-8")


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
        self.assertEqual(result["summary"]["case_count"], 10)
        self.assertEqual(result["summary"]["variant_count"], 3)
        self.assertEqual(result["repeat"], 1)
        self.assertEqual(result["measured_iterations"], 30)
        self.assertNotIn("name", result["variants"][0])
        self.assertNotIn("multiplier", json.dumps(result))
        leader = result["variants"][0]
        self.assertEqual(leader["sample_count"], 10)
        self.assertEqual(leader["ci95_method"], "seeded-bootstrap")
        self.assertEqual(leader["bootstrap_resamples"], 10_000)
        self.assertEqual(result["leading_variant_ids"], ["v_02", "v_03"])
        for comparison in result["baseline_comparisons"]:
            self.assertEqual(comparison["mean_uplift"], 0.8)
            self.assertEqual(comparison["uplift_ci95_lower"], 0.5)
            self.assertEqual(comparison["uplift_ci95_upper"], 1.0)
            self.assertTrue(comparison["conclusive"])

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
        self.assertEqual(result["baseline_comparisons"][0]["mean_uplift"], 1.0)

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

    def test_generates_complete_matrix_with_provider_provenance(self):
        generation_cases = self.write_jsonl(
            "generation.jsonl", [{"id": "c", "input": "Answer from context: kafka"}]
        )
        templates = self.write_json(
            "templates.json",
            {
                "schema_version": 1,
                "templates": {
                    "v_01": {"system": "answer", "user_template": "{input}"},
                    "v_02": {"system": "extract", "user_template": "Q: {input}"},
                },
            },
        )
        output = Path(self.temp_dir.name, "outputs.jsonl")
        provenance = Path(self.temp_dir.name, "provenance.json")
        requests = []

        def opener(request: Request, _timeout: float):
            requests.append(json.loads(request.data.decode("utf-8")))
            return FakeResponse(
                {
                    "choices": [{"message": {"content": "kafka"}}],
                    "usage": {"prompt_tokens": 7, "completion_tokens": 1},
                }
            )

        generator = OpenAICompatibleGenerator(
            provider_id="test-provider",
            base_url="http://provider.test/v1",
            model="test-model",
            model_digest="sha256:" + "a" * 64,
            timeout_seconds=1,
            opener=opener,
        )
        result = generate_output_matrix(
            generator=generator,
            cases_path=generation_cases,
            templates_path=templates,
            variant_ids=["v_01", "v_02"],
            output_path=output,
            provenance_path=provenance,
            warmup_iterations=1,
            producer_source_commit="b" * 40,
            producer_image_digest="sha256:" + "c" * 64,
        )

        self.assertEqual(len(requests), 3)
        self.assertEqual(len(output.read_text(encoding="utf-8").splitlines()), 2)
        self.assertEqual(result["generation"]["measured_requests"], 2)
        self.assertEqual(result["generation"]["failures"], 0)
        self.assertEqual(result["generation"]["prompt_tokens"], 14)
        self.assertEqual(result["provider"]["model"], "test-model")
        self.assertEqual(result["producer"]["source_commit"], "b" * 40)
        self.assertEqual(
            result["artifacts"]["outputs_sha256"],
            json.loads(provenance.read_text(encoding="utf-8"))["artifacts"][
                "outputs_sha256"
            ],
        )

    def test_rejects_template_variant_mismatch(self):
        generation_cases = self.write_jsonl(
            "generation.jsonl", [{"id": "c", "input": "input"}]
        )
        templates = self.write_json(
            "templates.json",
            {
                "schema_version": 1,
                "templates": {
                    "v_01": {"system": "answer", "user_template": "{input}"},
                    "v_03": {"system": "answer", "user_template": "{input}"},
                },
            },
        )
        generator = OpenAICompatibleGenerator(
            provider_id="test",
            base_url="http://provider.test/v1",
            model="model",
            model_digest="sha256:" + "a" * 64,
            timeout_seconds=1,
        )
        with self.assertRaisesRegex(GenerationValidationError, "must match"):
            generate_output_matrix(
                generator=generator,
                cases_path=generation_cases,
                templates_path=templates,
                variant_ids=["v_01", "v_02"],
                output_path=Path(self.temp_dir.name, "outputs.jsonl"),
                provenance_path=Path(self.temp_dir.name, "provenance.json"),
            )


if __name__ == "__main__":
    unittest.main()
