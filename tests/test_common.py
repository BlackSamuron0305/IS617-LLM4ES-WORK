"""Tests for the shared helpers (pipeline/common.py)."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from pipeline.common import (EXPERIMENT, ROOT, append_jsonl, dirty_files, git_commit, last_by_key, load_models,
                             messages_sha256, read_jsonl, read_table, read_text, sha256_text, utc_now, write_csv)


class CommonTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def test_read_jsonl_missing_is_empty(self):
        self.assertEqual(read_jsonl(self.tmp / "nope.jsonl"), [])

    def test_append_and_last_by_key(self):
        p = self.tmp / "deeper" / "raw.jsonl"
        append_jsonl(p, {"key": "a", "v": 1})
        append_jsonl(p, {"key": "a", "v": 2})
        append_jsonl(p, {"key": "b", "v": 3})
        self.assertEqual(len(read_jsonl(p)), 3)
        self.assertEqual({k: r["v"] for k, r in last_by_key(read_jsonl(p)).items()}, {"a": 2, "b": 3})

    def test_append_jsonl_keeps_non_ascii_on_one_line(self):
        p = self.tmp / "u.jsonl"
        append_jsonl(p, {"key": "a", "text": "Qatari – قطر"})
        raw = p.read_text(encoding="utf-8")
        self.assertEqual(raw.count("\n"), 1)
        self.assertIn("قطر", raw)

    def test_write_csv_roundtrip(self):
        p = self.tmp / "out" / "t.csv"
        rows = [{"a": "1", "b": "x, y"}, {"a": "2", "b": "é"}]
        write_csv(p, rows, ["a", "b"])
        self.assertEqual(read_table(p), rows)

    def test_read_text_and_table(self):
        self.assertIn("alias", read_text(EXPERIMENT / "models.csv"))
        self.assertEqual(len(read_table(EXPERIMENT / "models.csv")), 4)

    def test_load_models_parses_extra_body(self):
        models = load_models(EXPERIMENT / "models.csv")
        self.assertEqual(models["qwen3-8b"]["extra_body"], {"chat_template_kwargs": {"enable_thinking": False}})
        self.assertEqual(models["llama-3.1-8b-instruct"]["extra_body"], {})

    def test_messages_sha256_stable(self):
        m = [{"role": "user", "content": "x"}]
        self.assertEqual(messages_sha256(m), messages_sha256([{"content": "x", "role": "user"}]))
        self.assertEqual(messages_sha256(m), sha256_text('[{"content": "x", "role": "user"}]'))

    def test_utc_now_format(self):
        self.assertRegex(utc_now(), r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_git_commit(self):
        self.assertRegex(git_commit(ROOT), r"^[0-9a-f]{40}$")
        self.assertEqual(git_commit(self.tmp), "")

    def test_dirty_files_sees_untracked_file_in_watched_folder(self):
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True)
        self.assertEqual(dirty_files(self.tmp), [])
        (self.tmp / "experiment").mkdir()
        (self.tmp / "experiment" / "x.txt").write_text("x", encoding="utf-8")
        (self.tmp / "elsewhere.txt").write_text("y", encoding="utf-8")
        lines = dirty_files(self.tmp)
        self.assertEqual(len(lines), 1)
        self.assertIn("experiment", lines[0])

    def test_dirty_files_is_not_clean_when_git_fails(self):
        self.assertNotEqual(dirty_files(self.tmp), [])


if __name__ == "__main__":
    unittest.main()
