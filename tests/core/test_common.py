"""Tests for the shared helpers (pipeline/core/common.py)."""

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

from pipeline.core.common import (EXPERIMENT, ROOT, append_jsonl, dirty_files, git_commit, last_by_key, load_models,
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

    def test_append_jsonl_writes_plain_lines_without_blank_ones(self):
        p = self.tmp / "plain.jsonl"
        append_jsonl(p, {"key": "a"})
        append_jsonl(p, {"key": "b"})
        self.assertEqual(p.read_bytes(), b'{"key": "a"}\n{"key": "b"}\n')

    def test_read_jsonl_skips_a_torn_last_line_and_warns(self):
        p = self.tmp / "torn.jsonl"
        p.write_text('{"key": "a", "v": 1}\n{"key": "b", "err', encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()) as err:
            records = read_jsonl(p)
        self.assertEqual(records, [{"key": "a", "v": 1}])
        self.assertEqual(err.getvalue(), f"skipped 1 unreadable line(s) in {p}\n")

    def test_read_jsonl_skips_a_line_torn_inside_a_character(self):
        p = self.tmp / "torn_bytes.jsonl"
        p.write_bytes('{"key": "a"}\n'.encode("utf-8") + '{"key": "b", "text": "قطر"}'.encode("utf-8")[:-6])
        with contextlib.redirect_stderr(io.StringIO()) as err:
            records = read_jsonl(p)
        self.assertEqual(records, [{"key": "a"}])
        self.assertIn("skipped 1 unreadable line(s)", err.getvalue())

    def test_read_jsonl_is_silent_when_every_line_is_readable(self):
        p = self.tmp / "fine.jsonl"
        append_jsonl(p, {"key": "a"})
        with contextlib.redirect_stderr(io.StringIO()) as err:
            read_jsonl(p)
        self.assertEqual(err.getvalue(), "")

    def test_append_after_a_torn_line_keeps_the_new_record_readable(self):
        p = self.tmp / "torn.jsonl"
        p.write_text('{"key": "a", "v": 1}\n{"key": "b", "err', encoding="utf-8")
        append_jsonl(p, {"key": "b", "v": 2})
        self.assertEqual(p.read_bytes().count(b"\n"), 3)  # the fragment ends its own line
        with contextlib.redirect_stderr(io.StringIO()):
            records = read_jsonl(p)
        self.assertEqual(records, [{"key": "a", "v": 1}, {"key": "b", "v": 2}])

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
        self.assertIn("alias", read_text(EXPERIMENT / "config/models.csv"))
        self.assertEqual(len(read_table(EXPERIMENT / "config/models.csv")), 23)

    def test_load_models_parses_extra_body(self):
        # A file of the test's own: the rows of experiment/config/models.csv may change.
        path = self.tmp / "models.csv"
        write_csv(path, [{"alias": "a", "model_id": "o/a", "revision": "", "extra_body": '{"x": {"y": false}}'},
                         {"alias": "b", "model_id": "o/b", "revision": "", "extra_body": ""}],
                  ["alias", "model_id", "revision", "extra_body"])
        models = load_models(path)
        self.assertEqual(models["a"]["extra_body"], {"x": {"y": False}})
        self.assertEqual(models["b"]["extra_body"], {})
        live = load_models(EXPERIMENT / "config/models.csv")  # the live file loads, whatever its rows say
        self.assertEqual(set(live), {row["alias"] for row in read_table(EXPERIMENT / "config/models.csv")})

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
