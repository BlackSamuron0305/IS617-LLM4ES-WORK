"""Tests for the confirmatory analysis. Mock batches only show that the code runs; they are not results."""

import contextlib
import io
import random
import tempfile
import unittest
from pathlib import Path

from pipeline.analysis.analyze_main import (adjusted_rand, analyse_model, holm, load, main, ranks, spearman, three_way_split)
from pipeline.core.client import MockClient
from pipeline.answers.parse_answers import parse_batch
from pipeline.answers.run_models import run_answers


class HelpersTest(unittest.TestCase):
    def test_ranks_and_spearman(self):
        self.assertEqual(ranks([10, 20, 20, 30]), [1.0, 2.5, 2.5, 4.0])
        self.assertAlmostEqual(spearman([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)
        self.assertAlmostEqual(spearman([1, 2, 3, 4], [1, 2, 3, 4]), 1.0)

    def test_adjusted_rand_is_one_for_the_same_partition(self):
        self.assertAlmostEqual(adjusted_rand([1, 1, 2, 2, 3, 3], [3, 3, 1, 1, 2, 2]), 1.0)
        self.assertLess(adjusted_rand([1, 1, 2, 2, 3, 3], [1, 2, 3, 1, 2, 3]), 0.2)

    def test_three_way_split_cuts_at_the_two_largest_gaps(self):
        means = {"a": 0, "b": 1, "c": 2, "d": 20, "e": 21, "f": 50}
        split = three_way_split(means)
        self.assertEqual(split["a"], split["b"])
        self.assertEqual(split["a"], split["c"])
        self.assertEqual(len({split["a"], split["d"], split["f"]}), 3)
        self.assertEqual(split["f"], 1)  # the highest group is "rich"

    def test_holm(self):
        self.assertEqual(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])


class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        run_answers("mock_main", "qwen3-32b", MockClient("answers"), cls.tmp, blocks=[1, 2, 3], mock=True,
                    wordings=[1], max_repetitions=1)
        with contextlib.redirect_stdout(io.StringIO()):
            parse_batch("mock_main", cls.tmp)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_all_four_hypotheses_run_on_a_mock_batch(self):
        _, ok = load("mock_main", self.tmp)
        lines, out = analyse_model("qwen3-32b", ok, 20, random.Random(1))
        text = "\n".join(lines)
        for part in ("H1 spread among 21 nationalities", "H2 Spearman", "H3 spread with the paragraph", "H4 score at AED"):
            self.assertIn(part, text)
        self.assertTrue(0 < out["h1_p"] <= 1)

    def test_cli(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = main(["--batch", "mock_main", "--permutations", "10", "--data-root", str(self.tmp)])
        self.assertEqual(code, 0)
        self.assertIn("MOCK BATCH, NOT A RESULT", out.getvalue())
        self.assertIn("after Holm correction", out.getvalue())

    def test_missing_batch_returns_2(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--batch", "mock_none", "--data-root", str(self.tmp)]), 2)


if __name__ == "__main__":
    unittest.main()
