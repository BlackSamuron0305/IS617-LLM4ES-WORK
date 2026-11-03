"""Tests for the judge lab: build, run (mock), parse and compare. A mock judge only shows that the code runs."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from pipeline import judge_lab
from pipeline.client import MockClient
from pipeline.parse_answers import parse_batch
from pipeline.run_models import run_answers


class JudgeLabTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        run_answers("mock_lab", "qwen3-32b", MockClient("answers"), cls.tmp, blocks=[1], mock=True, wordings=[1], max_repetitions=1, limit=120)
        with contextlib.redirect_stdout(io.StringIO()):
            parse_batch("mock_lab", cls.tmp)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_versions_have_prompts_with_every_code(self):
        for version, cfg in judge_lab.versions().items():
            prompt = (judge_lab.LAB / f"{version}_prompt.txt").read_text(encoding="utf-8") if version.startswith("v1") else None
            task = (judge_lab.LAB / f"{version}_task.txt").read_text(encoding="utf-8")
            for code in cfg["codes"]:
                self.assertIn(f'"{code}"', task, (version, code))
            self.assertEqual(task.count("{application}"), 1)
            self.assertEqual(task.count("{reason}"), 1)

    def test_build_run_parse_and_compare_unmasked_version(self):
        built = judge_lab.build("mock_lab", "v1_unmasked", self.tmp, blocks=["1"])
        self.assertGreater(built["items"], 0)
        # unmasked: the nationality is in the application the judge sees
        items = (self.tmp / "processed/mock_lab/lab_v1_unmasked_items.jsonl").read_text(encoding="utf-8")
        self.assertIn("Nationality: ", items)
        self.assertNotIn("Nationality: [NATIONALITY]", items)
        with contextlib.redirect_stdout(io.StringIO()):
            judge_lab.run("mock_lab", "v1_unmasked", "olmo-3.1-32b-instruct", MockClient("judge"), self.tmp, mock=True)
        status = judge_lab.parse("mock_lab", "v1_unmasked", "olmo-3.1-32b-instruct", self.tmp)
        self.assertGreater(status.get("ok", 0), 0)
        rows = judge_lab.compare("mock_lab", "v1_unmasked:olmo-3.1-32b-instruct", "v1_unmasked:olmo-3.1-32b-instruct", self.tmp)
        self.assertEqual({r["code"] for r in rows}, set(judge_lab.versions()["v1_unmasked"]["codes"]))
        self.assertTrue(all(r["agreement"] == 1.0 for r in rows))

    def test_masked_version_hides_the_nationality(self):
        judge_lab.build("mock_lab", "v2", self.tmp, blocks=["1"])
        items = (self.tmp / "processed/mock_lab/lab_v2_items.jsonl").read_text(encoding="utf-8")
        self.assertIn("Nationality: [NATIONALITY]", items)
        self.assertIn("Funds required for this stay", items)


if __name__ == "__main__":
    unittest.main()
