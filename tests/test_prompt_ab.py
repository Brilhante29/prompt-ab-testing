import unittest
from prompt_ab_testing.cli import evaluate

class PromptABTests(unittest.TestCase):
    def test_grounded_variant_wins(self):
        result = evaluate()
        self.assertEqual(result["best_variant"], "B")
        self.assertGreaterEqual(result["best_variant_score"], 0.9)

if __name__ == "__main__":
    unittest.main()
