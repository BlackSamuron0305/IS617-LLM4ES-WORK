"""Tests for the run_judge and judge_parse stages. No real model is called: every run uses the
mock client or a client defined in the test; the processed files are built by hand or from a
mock answers run."""

import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline.judge import build as judge_build
from pipeline.core.client import MockClient, OpenAICompatibleClient, RunRefused
from pipeline.core.common import append_jsonl, load_models, load_settings, read_jsonl, read_table, write_csv
from pipeline.judge.build import JUDGE, JUDGE_CODES, LINK_COLUMNS, build_judge_items
from pipeline.judge.parse import (JUDGE_CODE_COLUMNS, JUDGE_SCHEMA, main as judge_parse_main, parse_judge,
                                  parse_judge_answer)
from pipeline.answers.parse_answers import ANSWER_COLUMNS, parse_batch
from pipeline.judge.run import main as run_judge_main, run_judge
from pipeline.answers.run_models import run_answers

OK = ('{"mentions_nationality": "YES", "nationality_as_risk": "no", "passport_country_conditions": "no", '
      '"doubts_residence": "no", "contradicts_application": "no", "names_legal_ground": "no", '
      '"evidence": "a [NATIONALITY] passport"}')
ALL_NO = dict.fromkeys(JUDGE_CODES, "no")
# The judge models as the live experiment/judge/judge_models.csv has them (revision, extra_body ...).
JUDGES = load_models(JUDGE / "judge_models.csv")
PRIMARY = JUDGES["olmo-3.1-32b-instruct"]
JUDGED_COLUMNS = [*ANSWER_COLUMNS, "item_id", "n_masked", "judge_status", *JUDGE_CODES]


def quietly(function, *args, **kwargs):
    # The stages print counts and summaries; the tests keep that out of the test output.
    with contextlib.redirect_stdout(io.StringIO()):
        return function(*args, **kwargs)


def run_cli(main, argv):
    with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def write_jsonl(path, records):
    # pipeline.judge.build.write_jsonl for a folder that may not exist yet.
    path.parent.mkdir(parents=True, exist_ok=True)
    judge_build.write_jsonl(path, records)


def read_rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


class ParseJudgeAnswerTest(unittest.TestCase):
    def test_parse_judge_answer(self):
        self.assertEqual(parse_judge_answer(OK, None), {"judge_status": "ok", "mentions_nationality": 1,
                                                        "nationality_as_risk": 0, "passport_country_conditions": 0,
                                                        "doubts_residence": 0, "contradicts_application": 0,
                                                        "names_legal_ground": 0,
                                                        "evidence": "a [NATIONALITY] passport"})
        j = json.loads(OK)
        self.assertEqual(parse_judge_answer(json.dumps(dict(j, doubts_residence="maybe")), None)["judge_status"],
                         "bad_value")
        self.assertEqual(parse_judge_answer(json.dumps({k: v for k, v in j.items() if k != "doubts_residence"}),
                                            None)["judge_status"], "missing_key")
        self.assertEqual(parse_judge_answer(json.dumps({k: v for k, v in j.items() if k != "evidence"}),
                                            None)["evidence"], "")
        self.assertEqual(parse_judge_answer(json.dumps(dict(j, mentions_nationality="no",
                                                            nationality_as_risk="yes")), None)["judge_status"],
                         "inconsistent")
        self.assertEqual(parse_judge_answer(None, "ClientError: x")["judge_status"], "call_error")

    def test_no_json_and_text_around_the_object(self):
        self.assertEqual(parse_judge_answer("I cannot code this.", None)["judge_status"], "no_json")
        self.assertEqual(parse_judge_answer("", None)["judge_status"], "no_json")
        self.assertEqual(parse_judge_answer(None, None)["judge_status"], "no_json")
        fenced = parse_judge_answer(f"Here you go:\n```json\n{OK}\n```", None)
        self.assertEqual((fenced["judge_status"], fenced["mentions_nationality"]), ("ok", 1))

    def test_values_are_stripped_and_lower_cased(self):
        j = dict(json.loads(OK), nationality_as_risk=" Yes ", mentions_nationality="YES")
        out = parse_judge_answer(json.dumps(j), None)
        self.assertEqual((out["judge_status"], out["nationality_as_risk"]), ("ok", 1))

    def test_not_yes_or_no_is_bad_value(self):
        j = json.loads(OK)
        for value in ("maybe", "", True, 1, None, ["yes"]):
            out = parse_judge_answer(json.dumps(dict(j, doubts_residence=value)), None)
            self.assertEqual(out["judge_status"], "bad_value", value)

    def test_status_order_first_that_applies_wins(self):
        j = json.loads(OK)
        # error beats everything, a missing key beats a bad value, a bad value beats an inconsistency
        self.assertEqual(parse_judge_answer(OK, "ClientError: x")["judge_status"], "call_error")
        both = {k: v for k, v in j.items() if k != "doubts_residence"}
        both["contradicts_application"] = "maybe"
        self.assertEqual(parse_judge_answer(json.dumps(both), None)["judge_status"], "missing_key")
        bad_and_inconsistent = dict(j, mentions_nationality="no", nationality_as_risk="yes", doubts_residence="x")
        self.assertEqual(parse_judge_answer(json.dumps(bad_and_inconsistent), None)["judge_status"], "bad_value")

    def test_inconsistent_keeps_the_codes(self):
        out = parse_judge_answer(json.dumps(dict(json.loads(OK), mentions_nationality="no",
                                                 nationality_as_risk="yes")), None)
        self.assertEqual((out["mentions_nationality"], out["nationality_as_risk"]), (0, 1))

    def test_codes_are_blank_when_the_status_is_not_ok_or_inconsistent(self):
        j = json.loads(OK)
        for text, error in ((None, "ClientError: x"), ("no json here", None),
                            (json.dumps({k: v for k, v in j.items() if k != "doubts_residence"}), None),
                            (json.dumps(dict(j, doubts_residence="maybe")), None)):
            out = parse_judge_answer(text, error)
            self.assertEqual([out[code] for code in JUDGE_CODES], [""] * len(JUDGE_CODES))
            self.assertNotEqual(out["judge_status"], "ok")

    def test_evidence_is_kept_when_a_string_else_blank(self):
        j = json.loads(OK)
        self.assertEqual(parse_judge_answer(json.dumps(dict(j, doubts_residence="maybe")), None)["evidence"],
                         "a [NATIONALITY] passport")
        self.assertEqual(parse_judge_answer(json.dumps(dict(j, evidence=["a", "b"])), None)["evidence"], "")
        self.assertEqual(parse_judge_answer(json.dumps(dict(j, evidence=None)), None)["evidence"], "")

    def test_schema(self):
        self.assertEqual(list(JUDGE_SCHEMA["properties"]), [*JUDGE_CODES, "evidence"])
        for code in JUDGE_CODES:
            self.assertEqual(JUDGE_SCHEMA["properties"][code], {"type": "string", "enum": ["yes", "no"]})
        self.assertEqual(JUDGE_SCHEMA["properties"]["evidence"], {"type": "string"})
        self.assertEqual(JUDGE_SCHEMA["required"], [*JUDGE_CODES, "evidence"])
        self.assertIs(JUDGE_SCHEMA["additionalProperties"], False)

    def test_columns(self):
        self.assertEqual(JUDGE_CODE_COLUMNS, ["item_id", "applicant_id", "n_masked", "reason_masked", "judge_status",
                                              *JUDGE_CODES, "evidence"])


class RunJudgeTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def write_items(self, batch, n=5):
        items = [{"item_id": f"item{i}", "applicant_id": "A01", "reason_masked": f"reason {i}", "n_masked": 0,
                  "system": "SYSTEM", "user": f"USER {i}"} for i in range(n)]
        write_jsonl(self.tmp / "processed" / batch / "judge_items.jsonl", items)
        return items

    def mock_run(self, batch="mock_j", alias="olmo-3.1-32b-instruct", **kwargs):
        return run_judge(batch, alias, MockClient("judge"), self.tmp, mock=True, **kwargs)

    def raw(self, batch="mock_j", alias="olmo-3.1-32b-instruct"):
        return self.tmp / "raw" / batch / f"judge_{alias}.jsonl"

    def manifest(self, batch="mock_j", alias="olmo-3.1-32b-instruct"):
        return json.loads((self.tmp / "raw" / batch / f"judge_{alias}_manifest.json").read_text(encoding="utf-8"))

    def test_mock_run_writes_labelled_records(self):
        self.write_items("mock_j")
        summary = self.mock_run()
        self.assertEqual(summary, {"planned": 5, "already_done": 0, "called": 5, "errors": 0})
        records = read_jsonl(self.raw())
        self.assertEqual({r["key"] for r in records}, {f"item{i}" for i in range(5)})
        self.assertTrue(all(r["mock"] and r["kind"] == "judge" and r["model_alias"] == "olmo-3.1-32b-instruct"
                            and r["batch"] == "mock_j" and r["model_id"] == PRIMARY["model_id"]
                            and r["item_id"] == r["key"] for r in records))
        self.assertTrue(all(r["error"] is None and r["text"] for r in records))
        # Judge settings (run_settings.csv) and the judge model's extra_body (judge_models.csv).
        params = records[0]["params"]
        settings = load_settings("judge")
        self.assertEqual((params["temperature"], params["top_p"], params["max_tokens"], params["seed"]),
                         (settings["temperature"], settings["top_p"], settings["max_tokens"], settings["seed"]))
        self.assertEqual({key: params[key] for key in PRIMARY["extra_body"]}, PRIMARY["extra_body"])
        self.assertEqual("response_format" in params, settings["json_schema"])

    def test_the_other_judge_gets_its_own_files_and_extra_body(self):
        self.write_items("mock_j", 2)
        self.mock_run(alias="gpt-oss-120b")
        self.assertTrue(self.raw(alias="gpt-oss-120b").exists())
        self.assertFalse(self.raw().exists())
        other = JUDGES["gpt-oss-120b"]["extra_body"]
        params = read_jsonl(self.raw(alias="gpt-oss-120b"))[0]["params"]
        self.assertEqual({key: params[key] for key in other}, other)

    def test_sends_system_and_user_of_the_item(self):
        self.write_items("mock_j", 1)

        class Recording(MockClient):
            def __init__(self, kind):
                super().__init__(kind)
                self.sent = []

            def complete(self, messages, params):
                self.sent.append(messages)
                return super().complete(messages, params)

        client = Recording("judge")
        run_judge("mock_j", "olmo-3.1-32b-instruct", client, self.tmp, mock=True)
        self.assertEqual(client.sent, [[{"role": "system", "content": "SYSTEM"},
                                        {"role": "user", "content": "USER 0"}]])

    def test_manifest_has_header_and_session_with_summary(self):
        self.write_items("mock_j", 3)
        self.mock_run(limit=2)
        stored = self.manifest()
        self.assertEqual({k: stored[k] for k in ("batch", "kind", "model_alias", "model_id", "revision", "mock")},
                         {"batch": "mock_j", "kind": "judge", "model_alias": "olmo-3.1-32b-instruct",
                          "model_id": PRIMARY["model_id"], "revision": PRIMARY["revision"], "mock": True})
        (session,) = stored["sessions"]
        self.assertEqual(session["limit"], 2)
        self.assertEqual(session["settings"], load_settings("judge"))
        self.assertEqual(session["summary"], {"planned": 2, "already_done": 0, "called": 2, "errors": 0})
        for field in ("started_utc", "git_commit", "dirty"):
            self.assertIn(field, session)

    def test_limit_takes_the_first_items(self):
        self.write_items("mock_j", 5)
        self.mock_run(limit=2)
        self.assertEqual({r["key"] for r in read_jsonl(self.raw())}, {"item0", "item1"})

    def test_resume_skips_done_and_retries_errors(self):
        self.write_items("mock_j", 3)
        self.mock_run()
        recs = read_jsonl(self.raw())
        append_jsonl(self.raw(), dict(recs[0], error="ClientError: boom", text=None))
        again = self.mock_run()
        self.assertEqual((again["already_done"], again["called"]), (2, 1))
        self.assertEqual(len(self.manifest()["sessions"]), 2)

    def test_batch_started_with_another_model_id_or_revision_is_refused(self):
        # Each judge has its own manifest, so a second judge can run on the same batch ...
        self.write_items("mock_j", 2)
        self.mock_run()
        self.mock_run(alias="gpt-oss-120b")
        self.assertEqual(self.manifest(alias="gpt-oss-120b")["model_alias"], "gpt-oss-120b")
        # ... but a batch that was started with another revision (say, before it was pinned) is refused.
        before = self.raw().read_text(encoding="utf-8")
        path = self.tmp / "raw/mock_j/judge_olmo-3.1-32b-instruct_manifest.json"
        stored = json.loads(path.read_text(encoding="utf-8"))
        other_revision = "f" * 40 if stored["revision"] != "f" * 40 else "e" * 40
        path.write_text(json.dumps(dict(stored, revision=other_revision)), encoding="utf-8")
        with self.assertRaisesRegex(RunRefused, "revision"):
            self.mock_run()
        self.assertEqual(self.raw().read_text(encoding="utf-8"), before)

    def test_mock_labelling_guards(self):
        self.write_items("mock_j", 1)
        self.write_items("pilot1", 1)
        with self.assertRaisesRegex(RunRefused, "mock"):
            run_judge("mock_j", "olmo-3.1-32b-instruct", MockClient("judge"), self.tmp, mock=False)
        with self.assertRaisesRegex(RunRefused, "mock"):
            run_judge("mock_j", "olmo-3.1-32b-instruct", mock.Mock(), self.tmp, mock=True)
        with self.assertRaisesRegex(RunRefused, "mock"):
            run_judge("pilot1", "olmo-3.1-32b-instruct", MockClient("judge"), self.tmp, mock=True)
        self.assertFalse((self.tmp / "raw").exists())

    def test_unknown_alias_is_refused(self):
        self.write_items("mock_j", 1)
        with self.assertRaisesRegex(RunRefused, "nope"):
            self.mock_run(alias="nope")
        self.assertFalse((self.tmp / "raw").exists())

    def test_missing_items_file(self):
        with self.assertRaisesRegex(FileNotFoundError, "judge_items.jsonl"):
            self.mock_run()
        self.assertFalse((self.tmp / "raw").exists())

    def test_the_schema_goes_to_the_call_loop(self):
        self.write_items("mock_j", 1)
        with mock.patch("pipeline.judge.run.run_calls",
                        return_value={"planned": 0, "already_done": 0, "called": 0, "errors": 0}) as run_calls:
            self.mock_run()
        self.assertIs(run_calls.call_args.args[4], JUDGE_SCHEMA)

    # --- the command line

    def test_cli_refuses_real_judge_without_flag(self):
        self.write_items("pilot1", 1)
        with mock.patch.object(OpenAICompatibleClient, "served_models", side_effect=AssertionError("network")):
            code, _, err = run_cli(run_judge_main, ["--batch", "pilot1", "--judge", "olmo-3.1-32b-instruct", "--base-url",
                                                    "http://127.0.0.1:9/v1", "--data-root", str(self.tmp)])
        self.assertEqual(code, 2)
        self.assertIn("refusing: ", err)
        self.assertFalse((self.tmp / "raw").exists())

    def test_cli_refuses_real_judge_without_pinned_revision(self):
        # The flag is given, but the judge has no revision in its CSV: patched here, so that the test
        # does not depend on whether the team has pinned the revision in the live file.
        self.write_items("pilot1", 1)
        unpinned = {alias: dict(model, revision="") for alias, model in JUDGES.items()}
        with mock.patch("pipeline.judge.run.load_models", return_value=unpinned), \
                mock.patch.object(OpenAICompatibleClient, "served_models", side_effect=AssertionError("network")):
            code, _, err = run_cli(run_judge_main, ["--batch", "pilot1", "--judge", "olmo-3.1-32b-instruct", "--base-url",
                                                    "http://127.0.0.1:9/v1", "--allow-real-calls",
                                                    "--data-root", str(self.tmp)])
        self.assertEqual(code, 2)
        self.assertIn("refusing: ", err)
        self.assertIn("revision", err)
        self.assertIn("olmo-3.1-32b-instruct", err)
        self.assertFalse((self.tmp / "raw").exists())

    def test_a_real_client_built_by_hand_is_refused_and_nothing_is_written(self):
        # Only make_client approves a client; a client built directly cannot be used for a real run.
        self.write_items("pilot1", 1)
        client = OpenAICompatibleClient("http://127.0.0.1:9/v1", PRIMARY["model_id"])
        with mock.patch.object(OpenAICompatibleClient, "complete", side_effect=AssertionError("called")):
            with self.assertRaisesRegex(RunRefused, "make_client"):
                run_judge("pilot1", "olmo-3.1-32b-instruct", client, self.tmp, mock=False)
        self.assertFalse((self.tmp / "raw").exists())

    def test_cli_refuses_real_judge_without_flag_even_without_items(self):
        code, _, err = run_cli(run_judge_main, ["--batch", "pilot1", "--judge", "olmo-3.1-32b-instruct", "--base-url",
                                                "http://127.0.0.1:9/v1", "--data-root", str(self.tmp)])
        self.assertEqual(code, 2)
        self.assertIn("refusing: ", err)

    def test_cli_mock_run(self):
        self.write_items("mock_cli", 4)
        code, out, _ = run_cli(run_judge_main, ["--batch", "mock_cli", "--judge", "olmo-3.1-32b-instruct", "--limit", "3",
                                                "--mock", "--data-root", str(self.tmp)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["called"], 3)
        self.assertEqual(len(read_jsonl(self.raw("mock_cli"))), 3)

    def test_cli_unknown_judge_missing_items_and_bad_mock_batch(self):
        self.write_items("mock_cli", 1)
        self.write_items("pilot1", 1)
        code, _, err = run_cli(run_judge_main, ["--batch", "mock_cli", "--judge", "nope", "--mock",
                                                "--data-root", str(self.tmp)])
        self.assertEqual(code, 2)
        self.assertIn("nope", err)
        code, _, err = run_cli(run_judge_main, ["--batch", "mock_none", "--judge", "olmo-3.1-32b-instruct", "--mock",
                                                "--data-root", str(self.tmp)])
        self.assertEqual(code, 2)
        self.assertIn("judge_items.jsonl", err)
        self.assertEqual(run_cli(run_judge_main, ["--batch", "pilot1", "--judge", "olmo-3.1-32b-instruct", "--mock",
                                                  "--data-root", str(self.tmp)])[0], 2)
        self.assertFalse((self.tmp / "raw").exists())


class JudgeParseTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    # A hand-built batch: five answers, three judge inputs.
    #   a1, a2 -> i1 (judged ok), a3 -> no item (reason empty), a4 -> i2 (no judge record), a5 -> i3 (inconsistent)
    def build(self, batch="mock_h"):
        answers = []
        for key, applicant in (("a1", "A01"), ("a2", "A01"), ("a3", "A02"), ("a4", "A02"), ("a5", "A03")):
            row = dict.fromkeys(ANSWER_COLUMNS, "")
            row.update(batch=batch, key=key, run_id="run_" + key, repetition="1", applicant_id=applicant,
                       parse_status="ok", reason="r " + key)
            answers.append(row)
        write_csv(self.tmp / "processed" / batch / "answers.csv", answers, ANSWER_COLUMNS)
        links = [{"key": "a1", "run_id": "run_a1", "repetition": "1", "item_id": "i1", "n_masked": 2},
                 {"key": "a2", "run_id": "run_a2", "repetition": "1", "item_id": "i1", "n_masked": 2},
                 {"key": "a4", "run_id": "run_a4", "repetition": "1", "item_id": "i2", "n_masked": 0},
                 {"key": "a5", "run_id": "run_a5", "repetition": "1", "item_id": "i3", "n_masked": 1}]
        write_csv(self.tmp / "processed" / batch / "judge_links.csv", links, LINK_COLUMNS)
        items = [{"item_id": "i1", "applicant_id": "A01", "reason_masked": "masked 1", "n_masked": 2,
                  "system": "S", "user": "U1"},
                 {"item_id": "i2", "applicant_id": "A02", "reason_masked": "masked 2", "n_masked": 0,
                  "system": "S", "user": "U2"},
                 {"item_id": "i3", "applicant_id": "A03", "reason_masked": "masked 3", "n_masked": 1,
                  "system": "S", "user": "U3"}]
        write_jsonl(self.tmp / "processed" / batch / "judge_items.jsonl", items)

    def raw_path(self, batch="mock_h", alias="olmo-3.1-32b-instruct"):
        return self.tmp / "raw" / batch / f"judge_{alias}.jsonl"

    def add_record(self, item_id, text, error=None, batch="mock_h", alias="olmo-3.1-32b-instruct"):
        append_jsonl(self.raw_path(batch, alias), {"key": item_id, "item_id": item_id, "text": text, "error": error})

    def parse(self, batch="mock_h", alias="olmo-3.1-32b-instruct"):
        codes_path, judged_path = quietly(parse_judge, batch, alias, self.tmp)
        return read_rows(codes_path), read_rows(judged_path), codes_path, judged_path

    def test_join_statuses_and_columns(self):
        self.build()
        self.add_record("i1", OK)
        self.add_record("i3", json.dumps(dict(json.loads(OK), mentions_nationality="no", nationality_as_risk="yes")))
        codes, judged, codes_path, judged_path = self.parse()
        self.assertEqual(codes_path, self.tmp / "processed/mock_h/judge_codes_olmo-3.1-32b-instruct.csv")
        self.assertEqual(judged_path, self.tmp / "processed/mock_h/answers_judged_olmo-3.1-32b-instruct.csv")
        with open(codes_path, encoding="utf-8", newline="") as f:
            self.assertEqual(next(csv.reader(f)), JUDGE_CODE_COLUMNS)
        with open(judged_path, encoding="utf-8", newline="") as f:
            self.assertEqual(next(csv.reader(f)), JUDGED_COLUMNS)
        self.assertEqual([r["item_id"] for r in codes], ["i1", "i2", "i3"])
        self.assertEqual([r["judge_status"] for r in codes], ["ok", "not_run", "inconsistent"])
        self.assertEqual((codes[0]["applicant_id"], codes[0]["n_masked"], codes[0]["reason_masked"]),
                         ("A01", "2", "masked 1"))
        self.assertEqual((codes[0]["mentions_nationality"], codes[0]["evidence"]), ("1", "a [NATIONALITY] passport"))
        self.assertEqual([codes[1][c] for c in JUDGE_CODES], [""] * len(JUDGE_CODES))
        self.assertEqual((codes[2]["mentions_nationality"], codes[2]["nationality_as_risk"]), ("0", "1"))
        # every answer is kept, in the order of answers.csv, with its own columns first
        self.assertEqual([r["key"] for r in judged], ["a1", "a2", "a3", "a4", "a5"])
        self.assertEqual([r["judge_status"] for r in judged],
                         ["ok", "ok", "not_judged", "not_run", "inconsistent"])
        self.assertEqual([r["item_id"] for r in judged], ["i1", "i1", "", "i2", "i3"])
        self.assertEqual([r["n_masked"] for r in judged], ["2", "2", "", "0", "1"])
        self.assertEqual([r["mentions_nationality"] for r in judged], ["1", "1", "", "", "0"])
        self.assertEqual(judged[0]["reason"], "r a1")

    def test_last_record_wins_and_errors_show(self):
        self.build()
        self.add_record("i1", None, error="ClientError: boom")
        self.add_record("i2", "no json at all")
        self.add_record("i3", OK)
        self.assertEqual([r["judge_status"] for r in self.parse()[0]], ["call_error", "no_json", "ok"])
        self.add_record("i1", OK)  # a retry that worked
        self.assertEqual([r["judge_status"] for r in self.parse()[0]], ["ok", "no_json", "ok"])

    def test_missing_raw_file_means_nothing_was_run(self):
        self.build()
        codes, judged, _, _ = self.parse()
        self.assertEqual({r["judge_status"] for r in codes}, {"not_run"})
        self.assertEqual([r["judge_status"] for r in judged], ["not_run", "not_run", "not_judged", "not_run", "not_run"])

    def test_the_other_judge_is_a_separate_pair_of_files(self):
        self.build()
        self.add_record("i1", OK)
        self.add_record("i1", OK, alias="gpt-oss-120b")
        _, _, a, _ = self.parse()
        _, _, b, _ = self.parse(alias="gpt-oss-120b")
        self.assertNotEqual(a, b)
        self.assertTrue(a.exists() and b.exists())

    def test_missing_inputs_raise(self):
        self.build()
        for name in ("answers.csv", "judge_links.csv", "judge_items.jsonl"):
            (self.tmp / "processed/mock_h" / name).rename(self.tmp / "processed/mock_h" / (name + ".off"))
            with self.assertRaisesRegex(FileNotFoundError, name):
                quietly(parse_judge, "mock_h", "olmo-3.1-32b-instruct", self.tmp)
            (self.tmp / "processed/mock_h" / (name + ".off")).rename(self.tmp / "processed/mock_h" / name)

    def test_prints_counts_per_status(self):
        self.build()
        self.add_record("i1", OK)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            parse_judge("mock_h", "olmo-3.1-32b-instruct", self.tmp)
        text = out.getvalue()
        for line in ("  ok: 2", "  not_run: 2", "  not_judged: 1", "  ok: 1"):
            self.assertIn(line, text)

    # --- the command line

    def test_cli(self):
        self.build()
        self.add_record("i1", OK)
        code, out, _ = run_cli(judge_parse_main, ["--batch", "mock_h", "--judge", "olmo-3.1-32b-instruct",
                                                  "--data-root", str(self.tmp)])
        self.assertEqual(code, 0)
        self.assertIn("answers_judged_olmo-3.1-32b-instruct.csv", out)

    def test_cli_missing_inputs_and_unknown_judge(self):
        code, _, err = run_cli(judge_parse_main, ["--batch", "mock_h", "--judge", "olmo-3.1-32b-instruct",
                                                  "--data-root", str(self.tmp)])
        self.assertEqual(code, 2)
        self.assertIn("answers.csv", err)
        self.build()
        code, _, err = run_cli(judge_parse_main, ["--batch", "mock_h", "--judge", "olmo-3.1-32b-instruct",
                                                  "--data-root", str(self.tmp)])
        self.assertEqual(code, 2)
        self.assertIn("judge_olmo-3.1-32b-instruct.jsonl", err)
        code, _, err = run_cli(judge_parse_main, ["--batch", "mock_h", "--judge", "nope",
                                                  "--data-root", str(self.tmp)])
        self.assertEqual(code, 2)
        self.assertIn("nope", err)
        self.assertFalse((self.tmp / "processed/mock_h/judge_codes_olmo-3.1-32b-instruct.csv").exists())


class MockPipelineTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def test_mock_pipeline_end_to_end(self):
        tmp = self.tmp
        quietly(run_answers, "mock_e", "qwen3-32b", MockClient("answers"), tmp, blocks=[1], limit=80, mock=True)
        quietly(parse_batch, "mock_e", tmp)
        quietly(build_judge_items, "mock_e", tmp)
        summary = run_judge("mock_e", "olmo-3.1-32b-instruct", MockClient("judge"), tmp, mock=True)
        self.assertEqual(summary["errors"], 0)
        codes_path, judged_path = quietly(parse_judge, "mock_e", "olmo-3.1-32b-instruct", tmp)
        judged = read_rows(judged_path)
        self.assertEqual(len(judged), 80)
        self.assertIn("ok", {row["judge_status"] for row in judged})
        for row in judged:
            if row["judge_status"] == "ok":
                self.assertEqual(row["mentions_nationality"], "1" if int(row["n_masked"]) > 0 else "0")
            else:
                self.assertEqual(row["judge_status"], "not_judged")  # mock no_json answers have no item
        codes = read_table(codes_path)
        self.assertEqual({r["judge_status"] for r in codes}, {"ok"})
        self.assertEqual(len(codes), len(read_jsonl(tmp / "processed/mock_e/judge_items.jsonl")))

    def test_cli_chain_on_the_command_line(self):
        tmp = str(self.tmp)
        quietly(run_answers, "mock_c", "qwen3-32b", MockClient("answers"), self.tmp, blocks=[1], limit=20, mock=True)
        quietly(parse_batch, "mock_c", self.tmp)
        quietly(build_judge_items, "mock_c", self.tmp)
        self.assertEqual(run_cli(run_judge_main, ["--batch", "mock_c", "--judge", "gpt-oss-120b", "--mock",
                                                  "--data-root", tmp])[0], 0)
        self.assertEqual(run_cli(judge_parse_main, ["--batch", "mock_c", "--judge", "gpt-oss-120b",
                                                    "--data-root", tmp])[0], 0)
        self.assertTrue((self.tmp / "processed/mock_c/answers_judged_gpt-oss-120b.csv").exists())


if __name__ == "__main__":
    unittest.main()
