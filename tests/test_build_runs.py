"""Tests for the prompt builder (pipeline/build_runs.py). They call no model."""

import subprocess
import sys
import unittest

from pipeline.build_runs import build_runs
from pipeline.common import ROOT


class BuildRunsTest(unittest.TestCase):
    def test_counts_and_checks(self):
        runs, applicants, nationalities, problems = build_runs()
        self.assertEqual(problems, [])
        self.assertEqual(len(runs), 9360)
        self.assertEqual(sum(r["repetitions"] for r in runs), 21840)
        self.assertEqual(len({r["run_id"] for r in runs}), 9360)

    def test_one_known_prompt(self):
        runs = {r["run_id"]: r for r in build_runs()[0]}
        run = runs["b1__software_developer__s24000__SY__w1"]
        self.assertIn("Nationality: Syrian\n", run["user"])
        self.assertIn("Travel document: Syrian passport, valid until 2033", run["user"])

    def test_cli_passes(self):
        out = subprocess.run([sys.executable, "-m", "pipeline.build_runs"], capture_output=True, text=True,
                             encoding="utf-8", cwd=ROOT)
        self.assertEqual(out.returncode, 0)
        self.assertIn("all checks passed", out.stdout)


if __name__ == "__main__":
    unittest.main()
