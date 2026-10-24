"""Tests for the parse_answers stage. No real model is called: the raw answers come from the
mock client or are appended to the raw file by hand."""

import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline.build_runs import ANSWER_KEYS, CHECK_LETTERS
from pipeline.client import MockClient
from pipeline.common import append_jsonl, read_jsonl
from pipeline.parse_answers import ANSWER_COLUMNS, ANSWER_SCHEMA, extract_json, main, parse_answer, parse_batch
from pipeline.run_models import run_answers

VALID = '{"risk_score": 35, "risk_rating": "Medium ", "further_checks": ["c", "A"], "recommendation": "refer", "reason": "Short stay."}'
BLANK = {"risk_score": "", "risk_rating": "", "further_checks": "", "n_checks": "", "recommendation": ""}


def read_rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def run_cli(argv):
    with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class ParseAnswersTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def mock_run(self, batch="mock_p", limit=40):
        run_answers(batch, "qwen3-8b", MockClient("answers"), self.tmp, blocks=[1], limit=limit, mock=True)
        return self.tmp / "raw" / batch / "answers.jsonl"

    def parse(self, batch="mock_p"):
        with contextlib.redirect_stdout(io.StringIO()):
            return read_rows(parse_batch(batch, self.tmp))

    # --- extract_json

    def test_extract_variants(self):
        self.assertEqual(extract_json('{"a": 1}'), {"a": 1})
        self.assertEqual(extract_json('```json\n{"a": 1}\n```'), {"a": 1})
        self.assertEqual(extract_json('Sure! {"a": 1} Hope this helps'), {"a": 1})
        self.assertEqual(extract_json('<think>maybe {not json}</think>\n{"a": 1}'), {"a": 1})
        self.assertIsNone(extract_json("no json here"))
        self.assertIsNone(extract_json("[1, 2]"))

    def test_extract_takes_first_object_and_survives_broken_text(self):
        self.assertEqual(extract_json('{"a": 1} and then {"b": 2}'), {"a": 1})
        self.assertIsNone(extract_json('{"a": 1'))
        self.assertIsNone(extract_json(""))
        self.assertIsNone(extract_json(None))

    # --- parse_answer

    def test_parse_valid(self):
        self.assertEqual(parse_answer(VALID, None), {"parse_status": "ok", "risk_score": 35, "risk_rating": "medium",
                                                     "further_checks": "A;C", "n_checks": 2,
                                                     "recommendation": "refer", "reason": "Short stay."})

    def test_parse_statuses(self):
        j = json.loads(VALID)

        def status(**changes):
            return parse_answer(json.dumps(dict(j, **changes)), None)["parse_status"]

        self.assertEqual(status(risk_score=101), "bad_value")
        self.assertEqual(status(risk_score="35"), "bad_value")
        self.assertEqual(status(risk_score=True), "bad_value")
        self.assertEqual(status(risk_score=35.0), "ok")
        self.assertEqual(status(further_checks=["G"]), "bad_value")
        self.assertEqual(status(further_checks="A"), "bad_value")
        self.assertEqual(status(further_checks=[]), "ok")
        self.assertEqual(status(recommendation="approve"), "bad_value")
        self.assertEqual(parse_answer(json.dumps({k: v for k, v in j.items() if k != "reason"}), None)["parse_status"],
                         "missing_key")
        self.assertEqual(parse_answer(None, "ClientError: timeout")["parse_status"], "call_error")
        self.assertEqual(parse_answer("I cannot help", None)["parse_status"], "no_json")

    def test_parse_value_edges(self):
        j = json.loads(VALID)

        def parsed(**changes):
            return parse_answer(json.dumps(dict(j, **changes)), None)

        self.assertEqual(parsed(risk_score=0)["risk_score"], 0)
        self.assertEqual(parsed(risk_score=100)["risk_score"], 100)
        self.assertIsInstance(parsed(risk_score=35.0)["risk_score"], int)
        self.assertEqual(parsed(risk_score=-1)["parse_status"], "bad_value")
        self.assertEqual(parsed(risk_score=35.5)["parse_status"], "bad_value")
        self.assertEqual(parsed(risk_score=None)["parse_status"], "bad_value")
        # A check must be exactly one letter: "" and "AB" are substrings of the letters, but not checks.
        self.assertEqual(parsed(further_checks=[""])["parse_status"], "bad_value")
        self.assertEqual(parsed(further_checks=["AB"])["parse_status"], "bad_value")
        self.assertEqual(parsed(further_checks=[1])["parse_status"], "bad_value")
        self.assertEqual(parsed(risk_rating=3)["parse_status"], "bad_value")
        self.assertEqual(parsed(risk_rating="extreme")["parse_status"], "bad_value")
        self.assertEqual(parsed(reason=7)["parse_status"], "bad_value")
        # Duplicates and order do not matter; the checks are written sorted and unique.
        both = parsed(further_checks=["b", "B", " a "])
        self.assertEqual((both["further_checks"], both["n_checks"]), ("A;B", 2))
        none = parsed(further_checks=[])
        self.assertEqual((none["further_checks"], none["n_checks"]), ("", 0))
        self.assertEqual(parsed(recommendation=" REFUSE")["recommendation"], "refuse")

    def test_non_ok_rows_are_blank_except_reason(self):
        j = json.loads(VALID)
        bad = parse_answer(json.dumps(dict(j, risk_score=101)), None)
        self.assertEqual(bad, {"parse_status": "bad_value", **BLANK, "reason": "Short stay."})
        no_reason = parse_answer(json.dumps({k: v for k, v in j.items() if k != "reason"}), None)
        self.assertEqual(no_reason, {"parse_status": "missing_key", **BLANK, "reason": ""})
        missing = parse_answer(json.dumps({k: v for k, v in j.items() if k != "recommendation"}), None)
        self.assertEqual(missing, {"parse_status": "missing_key", **BLANK, "reason": "Short stay."})
        self.assertEqual(parse_answer("I cannot help", None), {"parse_status": "no_json", **BLANK, "reason": ""})
        self.assertEqual(parse_answer(None, "ClientError: timeout"),
                         {"parse_status": "call_error", **BLANK, "reason": ""})
        # A reason that is not a string is not kept.
        self.assertEqual(parse_answer(json.dumps(dict(j, reason=7)), None)["reason"], "")

    def test_error_wins_over_text(self):
        self.assertEqual(parse_answer(VALID, "ClientError: late")["parse_status"], "call_error")

    # --- the schema

    def test_answer_schema(self):
        self.assertEqual(ANSWER_SCHEMA["type"], "object")
        self.assertEqual(sorted(ANSWER_SCHEMA["required"]), sorted(ANSWER_KEYS))
        self.assertEqual(set(ANSWER_SCHEMA["properties"]), set(ANSWER_KEYS))
        self.assertIs(ANSWER_SCHEMA["additionalProperties"], False)
        props = ANSWER_SCHEMA["properties"]
        self.assertEqual(props["risk_score"], {"type": "integer", "minimum": 0, "maximum": 100})
        self.assertEqual(props["risk_rating"]["enum"], ["low", "medium", "high"])
        self.assertEqual(props["further_checks"], {"type": "array", "items": {"type": "string",
                                                                              "enum": list(CHECK_LETTERS)}})
        self.assertEqual(props["recommendation"]["enum"], ["grant", "refer", "refuse"])
        self.assertEqual(props["reason"], {"type": "string"})

    def test_run_answers_passes_the_schema_to_the_call_loop(self):
        with mock.patch("pipeline.run_models.run_calls",
                        return_value={"planned": 0, "already_done": 0, "called": 0, "errors": 0}) as run_calls:
            run_answers("mock_p", "qwen3-8b", MockClient("answers"), self.tmp, blocks=[1], limit=1, mock=True)
        self.assertIs(run_calls.call_args.args[4], ANSWER_SCHEMA)

    # --- parse_batch

    def test_parse_batch_end_to_end(self):
        self.mock_run()
        rows = self.parse()
        self.assertEqual(len(rows), 40)
        self.assertEqual(list(rows[0]), ANSWER_COLUMNS)
        self.assertTrue(all(r["prompt_matches"] == "1" for r in rows))
        self.assertEqual([r["key"] for r in rows], sorted(r["key"] for r in rows))
        statuses = {r["parse_status"] for r in rows}
        self.assertIn("ok", statuses)
        self.assertLessEqual(statuses, {"ok", "no_json"})
        first = rows[0]
        self.assertEqual((first["batch"], first["model_alias"], first["block"]), ("mock_p", "qwen3-8b", "1"))
        self.assertEqual(first["key"], first["run_id"] + "__r" + first["repetition"])
        self.assertTrue(first["applicant_id"] and first["country"] and first["wording"])
        ok = next(r for r in rows if r["parse_status"] == "ok")
        self.assertTrue(ok["reason"].startswith("MOCK ANSWER, NOT A RESULT."))
        self.assertIn(ok["risk_rating"], ("low", "medium", "high"))

    def test_parse_batch_prints_counts(self):
        self.mock_run()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            path = parse_batch("mock_p", self.tmp)
        self.assertEqual(path, self.tmp / "processed" / "mock_p" / "answers.csv")
        counts = {}
        for r in read_rows(path):
            counts[r["parse_status"]] = counts.get(r["parse_status"], 0) + 1
        for status, n in counts.items():
            self.assertIn(f"{status}: {n}", out.getvalue())
        self.assertIn("prompt_matches = 0: 0", out.getvalue())

    def test_changed_prompt_is_flagged(self):
        # The last record per key wins: a copy with another prompt hash replaces the first record.
        raw = self.mock_run(limit=1)
        (record,) = read_jsonl(raw)
        append_jsonl(raw, dict(record, prompt_sha256="x"))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            rows = read_rows(parse_batch("mock_p", self.tmp))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["prompt_matches"], "0")
        self.assertIn("prompt_matches = 0: 1", out.getvalue())

    def test_last_record_per_key_wins_and_errors_become_rows(self):
        raw = self.mock_run(limit=2)
        first, second = read_jsonl(raw)
        append_jsonl(raw, dict(first, text=None, finish_reason=None, error="ClientError: boom"))
        append_jsonl(raw, dict(second, text=VALID))
        rows = {r["key"]: r for r in self.parse()}
        self.assertEqual(len(rows), 2)
        self.assertEqual((rows[first["key"]]["parse_status"], rows[first["key"]]["error"]),
                         ("call_error", "ClientError: boom"))
        self.assertEqual(rows[second["key"]]["parse_status"], "ok")
        self.assertEqual(rows[second["key"]]["further_checks"], "A;C")
        self.assertEqual(rows[second["key"]]["prompt_matches"], "1")

    def test_awkward_reason_survives_csv(self):
        reason = 'Has a job, "stable" pay;\nسبب'
        raw = self.mock_run(limit=1)
        (record,) = read_jsonl(raw)
        append_jsonl(raw, dict(record, text=json.dumps(dict(json.loads(VALID), reason=reason), ensure_ascii=False)))
        rows = self.parse()
        self.assertEqual(rows[0]["parse_status"], "ok")
        self.assertEqual(rows[0]["reason"], reason)

    def test_record_with_unknown_run_id_is_kept_and_flagged(self):
        raw = self.mock_run(limit=1)
        (record,) = read_jsonl(raw)
        append_jsonl(raw, dict(record, key="nope__r1", run_id="nope"))
        rows = {r["key"]: r for r in self.parse()}
        self.assertEqual(rows["nope__r1"]["prompt_matches"], "0")
        self.assertEqual(rows["nope__r1"]["applicant_id"], "")
        self.assertEqual(rows[record["key"]]["prompt_matches"], "1")

    def test_missing_raw_file_is_an_error(self):
        with self.assertRaisesRegex(FileNotFoundError, "mock_none"):
            parse_batch("mock_none", self.tmp)
        self.assertFalse((self.tmp / "processed").exists())

    # --- the command line

    def test_cli(self):
        self.mock_run(limit=3)
        code, out, _ = run_cli(["--batch", "mock_p", "--data-root", str(self.tmp)])
        self.assertEqual(code, 0)
        self.assertIn("prompt_matches = 0: 0", out)
        self.assertEqual(len(read_rows(self.tmp / "processed/mock_p/answers.csv")), 3)

    def test_cli_missing_batch_returns_2(self):
        code, _, err = run_cli(["--batch", "mock_none", "--data-root", str(self.tmp)])
        self.assertEqual(code, 2)
        self.assertIn("mock_none", err)


if __name__ == "__main__":
    unittest.main()
