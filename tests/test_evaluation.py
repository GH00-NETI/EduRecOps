import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "packages"))
from edurec_core.evaluation import catalog_coverage, ndcg_at_k, recall_at_k


class EvaluationTests(unittest.TestCase):
    def test_recall(self):
        self.assertEqual(recall_at_k({"a", "b"}, ["a", "c", "b"], 2), 0.5)

    def test_ndcg_perfect_ranking(self):
        value = ndcg_at_k({"a": 3.0, "b": 2.0, "c": 1.0}, ["a", "b", "c"], 3)
        self.assertAlmostEqual(value, 1.0)

    def test_coverage(self):
        self.assertEqual(catalog_coverage([["a", "b"], ["b", "c"]], 4), 0.75)


if __name__ == "__main__":
    unittest.main()
