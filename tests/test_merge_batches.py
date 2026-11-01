import contextlib
import csv
import io
import tempfile
import unittest
from pathlib import Path

from pipeline.client import MockClient
from pipeline.merge_batches import main, merge
from pipeline.parse_answers import parse_batch
from pipeline.run_models import run_answers


class MergeTest(unittest.TestCase):
    def test_two_shards_become_one_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            for k in range(2):
                run_answers(f"mock_m_s{k}", "qwen3-32b", MockClient("answers"), tmp, blocks=[1], mock=True,
                            wordings=[1], max_repetitions=1, shard=(k, 2), limit=30)
                with contextlib.redirect_stdout(io.StringIO()):
                    parse_batch(f"mock_m_s{k}", tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                out = merge("mock_m", tmp)
            rows = list(csv.DictReader(open(out, encoding="utf-8", newline="")))
            self.assertEqual(len(rows), 60)
            self.assertEqual({r["batch"] for r in rows}, {"mock_m"})
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--into", "mock_none", "--data-root", str(tmp)]), 2)


if __name__ == "__main__":
    unittest.main()
