"""Tests for the pilot report. A mock batch only shows that the report runs; its numbers are not results."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from pipeline.client import MockClient
from pipeline.parse_answers import parse_batch
from pipeline.pilot_report import MIN_MONEY_STEP, main, money_step, report
from pipeline.run_models import run_answers


class PilotReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmp.name)
        # The pilot as it is meant to be run: blocks 1 and 3, wording 1, one repetition.
        run_answers("mock_pilot", "qwen3-32b", MockClient("answers"), cls.tmp, blocks=[1, 3], mock=True,
                    wordings=[1], max_repetitions=1)
        with contextlib.redirect_stdout(io.StringIO()):
            parse_batch("mock_pilot", cls.tmp)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_report_has_every_section_and_a_mock_label(self):
        lines, checks = report("mock_pilot", self.tmp)
        text = "\n".join(lines)
        self.assertTrue(text.startswith("MOCK BATCH, NOT A RESULT"))
        for part in ("1. Can the answers be read?", "2. Do the scores vary?", "3. Does the score react to money?",
                     "4. Plain applications", "5. Nationalities", "Go / no-go:"):
            self.assertIn(part, text)
        self.assertEqual(len(checks), 4)
        self.assertIn("3900 calls", text)
        self.assertIn("visa-exempt rows, read apart: ", text)

    def test_money_step_uses_every_level_of_a_cell(self):
        rows = []
        for level, score in (("2000", 40.0), ("3000", 70.0), ("4500", 70.0), ("7000", 70.0), ("10500", 70.0)):
            rows.append({"applicant_id": "a", "country": "Syria", "wording": "1", "savings": level, "score": score})
        steps = money_step(rows)
        self.assertEqual(list(steps), ["2000", "3000", "4500", "7000", "10500"])
        self.assertGreaterEqual(steps["3000"][0] - steps["2000"][0], MIN_MONEY_STEP)

    def test_cli_writes_the_report_and_returns_a_status(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = main(["--batch", "mock_pilot", "--data-root", str(self.tmp)])
        self.assertIn(code, (0, 1))
        self.assertIn("Go / no-go:", out.getvalue())
        self.assertTrue((self.tmp / "processed" / "mock_pilot" / "pilot_report.txt").exists())

    def test_missing_batch_returns_2(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--batch", "mock_none", "--data-root", str(self.tmp)]), 2)


if __name__ == "__main__":
    unittest.main()
