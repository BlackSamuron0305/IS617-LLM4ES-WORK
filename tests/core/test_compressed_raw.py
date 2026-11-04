"""A raw file kept compressed (answers.jsonl.gz, as in the repository) is read like the plain file."""

import gzip
import tempfile
import unittest
from pathlib import Path

from pipeline.core.calls import done_keys
from pipeline.core.common import read_jsonl


class CompressedRawFileTest(unittest.TestCase):
    def test_gz_is_read_when_the_plain_file_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "answers.jsonl"
            with gzip.open(str(path) + ".gz", "wb") as f:
                f.write(b'{"key": "a", "error": null}\n{"key": "b", "error": "boom"}\n')
            self.assertEqual([r["key"] for r in read_jsonl(path)], ["a", "b"])
            self.assertEqual(done_keys(path), {"a"})

    def test_the_plain_file_wins_when_both_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "answers.jsonl"
            with gzip.open(str(path) + ".gz", "wb") as f:
                f.write(b'{"key": "old", "error": null}\n')
            path.write_text('{"key": "new", "error": null}\n', encoding="utf-8")
            self.assertEqual([r["key"] for r in read_jsonl(path)], ["new"])

    def test_missing_file_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(read_jsonl(Path(tmp) / "none.jsonl"), [])


if __name__ == "__main__":
    unittest.main()
