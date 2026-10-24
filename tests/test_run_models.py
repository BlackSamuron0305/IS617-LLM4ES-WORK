"""Tests for the run settings, the call loop and the run_models stage. No real model is
called: every run uses the mock client or a client defined in the test."""

import contextlib
import io
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from pipeline.build_runs import build_runs
from pipeline.calls import done_keys, request_params, run_calls, update_manifest
from pipeline.client import ClientError, MockClient, OpenAICompatibleClient, RunRefused
from pipeline.common import EXPERIMENT, append_jsonl, load_settings, read_jsonl, read_text
from pipeline.run_models import main, plan_items, run_answers

SETTINGS = {"temperature": 0.7, "top_p": 1.0, "max_tokens": 400, "seed": "per_call", "json_schema": False}
MSGS = [{"role": "user", "content": "hi"}]


class CountingClient:
    # Answers every call with the same text and counts the calls (thread-safe).
    def __init__(self, fail_on=()):
        self.fail_on = set(fail_on)
        self.calls = 0
        self.lock = threading.Lock()

    def complete(self, messages, params):
        with self.lock:
            self.calls += 1
        if messages[-1]["content"] in self.fail_on:
            raise ClientError("boom")
        return {"text": "ok", "finish_reason": "stop", "served_model": "m", "usage": {"total_tokens": 1}}


def run_cli(argv):
    # main() prints to stdout and stderr; the tests keep that out of the test output.
    with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def item(key):
    return {"key": key, "messages": [{"role": "user", "content": key}], "meta": {"n": key}}


class RunModelsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def mock_run(self, batch="mock_t", model="qwen3-8b", limit=5, **kwargs):
        return run_answers(batch, model, MockClient("answers"), self.tmp, blocks=[1], limit=limit, mock=True, **kwargs)

    # --- settings and request parameters

    def test_load_settings(self):
        self.assertEqual(load_settings("judge"), {"temperature": 0.0, "top_p": 1.0, "max_tokens": 1000, "seed": 0,
                                                  "json_schema": False})
        self.assertEqual(load_settings("answers"), SETTINGS)

    def test_load_settings_rejects_bad_kind_and_value(self):
        with self.assertRaises(ValueError):
            load_settings("other")
        bad = self.tmp / "s.csv"
        bad.write_text(read_text(EXPERIMENT / "run_settings.csv").replace("json_schema,no,no", "json_schema,maybe,no"),
                       encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "json_schema"):
            load_settings("answers", bad)

    def test_request_params(self):
        s = SETTINGS
        p = request_params(s, "k1", {"chat_template_kwargs": {"enable_thinking": False}}, {"type": "object"})
        self.assertEqual(p["seed"], request_params(s, "k1", {}, None)["seed"])
        self.assertNotEqual(p["seed"], request_params(s, "k2", {}, None)["seed"])
        self.assertNotIn("response_format", p)
        self.assertIn("chat_template_kwargs", p)
        self.assertEqual((p["temperature"], p["top_p"], p["max_tokens"]), (0.7, 1.0, 400))
        with_schema = request_params(dict(s, json_schema=True), "k1", {}, {"type": "object"})
        self.assertEqual(with_schema["response_format"],
                         {"type": "json_schema", "json_schema": {"name": "answer", "schema": {"type": "object"}}})
        # The format is enforced only when the setting says yes and a schema is given.
        self.assertNotIn("response_format", request_params(dict(s, json_schema=True), "k1", {}, None))

    def test_request_params_fixed_seed(self):
        self.assertEqual(request_params(dict(SETTINGS, seed=0), "k1", {}, None)["seed"], 0)

    # --- planning

    def test_plan_items_repetitions_and_keys(self):
        runs = build_runs()[0]
        items = plan_items(runs, [1], None)
        self.assertEqual(len(items), 7800)
        self.assertEqual(items[0]["key"], items[0]["meta"]["run_id"] + "__r1")
        self.assertEqual(plan_items(runs, [3], 10)[9]["meta"]["block"], 3)
        first = items[0]
        self.assertEqual(first["meta"], {"run_id": runs[0]["run_id"], "repetition": 1, "block": 1})
        self.assertEqual([m["role"] for m in first["messages"]], ["system", "user"])
        self.assertEqual(first["messages"][0]["content"], runs[0]["system"])
        self.assertEqual(items[4]["meta"]["repetition"], 5)
        self.assertEqual(items[5]["meta"]["run_id"], runs[1]["run_id"])
        self.assertEqual(len(plan_items(runs, None, None)), 21840)

    # --- the call loop

    def test_run_calls_records_and_errors(self):
        out = self.tmp / "o.jsonl"
        client = CountingClient(fail_on={"b"})
        summary = run_calls([item("a"), item("b")], client, SETTINGS, {"x": 1}, None, out, 2, {"batch": "t"})
        self.assertEqual(summary, {"planned": 2, "already_done": 0, "called": 2, "errors": 1})
        recs = {r["key"]: r for r in read_jsonl(out)}
        self.assertEqual(recs["a"]["batch"], "t")
        self.assertEqual(recs["a"]["n"], "a")
        self.assertEqual(recs["a"]["text"], "ok")
        self.assertIsNone(recs["a"]["error"])
        self.assertEqual(recs["a"]["params"]["x"], 1)
        self.assertEqual(len(recs["a"]["prompt_sha256"]), 64)
        self.assertEqual(recs["b"]["error"], "ClientError: boom")
        self.assertIsNone(recs["b"]["text"])
        self.assertIsNone(recs["b"]["finish_reason"])
        for field in ("served_model", "usage", "started_utc", "finished_utc"):
            self.assertIn(field, recs["b"])
        self.assertEqual(done_keys(out), {"a"})

    def test_run_calls_skips_done_keys(self):
        out = self.tmp / "o.jsonl"
        run_calls([item("a")], CountingClient(), SETTINGS, {}, None, out, 1, {})
        client = CountingClient()
        summary = run_calls([item("a"), item("c")], client, SETTINGS, {}, None, out, 1, {})
        self.assertEqual(summary, {"planned": 2, "already_done": 1, "called": 1, "errors": 0})
        self.assertEqual(client.calls, 1)

    def test_run_calls_with_workers_writes_whole_lines(self):
        out = self.tmp / "o.jsonl"
        items = [item(f"k{i}") for i in range(60)]
        run_calls(items, CountingClient(), SETTINGS, {}, None, out, 8, {})
        self.assertEqual(sorted(r["key"] for r in read_jsonl(out)), sorted(i["key"] for i in items))

    # --- the manifest

    def test_update_manifest_appends_sessions_and_refuses_changed_header(self):
        path = self.tmp / "b" / "manifest.json"
        header = {"batch": "mock_t", "model_alias": "m1", "mock": True}
        update_manifest(path, header, {"started_utc": "t1"})
        update_manifest(path, header, {"started_utc": "t2"})
        stored = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(stored["model_alias"], "m1")
        self.assertEqual([s["started_utc"] for s in stored["sessions"]], ["t1", "t2"])
        with self.assertRaisesRegex(RunRefused, "model_alias"):
            update_manifest(path, dict(header, model_alias="m2"), {"started_utc": "t3"})
        self.assertEqual(len(json.loads(path.read_text(encoding="utf-8"))["sessions"]), 2)

    # --- run_answers

    def test_mock_run_writes_labelled_records(self):
        summary = self.mock_run(limit=30)
        self.assertEqual(summary["called"], 30)
        recs = read_jsonl(self.tmp / "raw/mock_t/answers.jsonl")
        self.assertEqual(len(recs), 30)
        self.assertTrue(all(r["mock"] for r in recs))
        self.assertTrue(all(r["kind"] == "answers" and r["model_alias"] == "qwen3-8b" and r["batch"] == "mock_t"
                            for r in recs))
        self.assertTrue(all(r["error"] is None and r["text"] for r in recs))
        # The model's extra_body from models.csv goes into the request.
        self.assertEqual(recs[0]["params"]["chat_template_kwargs"], {"enable_thinking": False})

    def test_manifest_has_header_and_session_with_summary(self):
        self.mock_run(limit=3)
        stored = json.loads((self.tmp / "raw/mock_t/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual({k: stored[k] for k in ("batch", "kind", "model_alias", "model_id", "revision", "mock")},
                         {"batch": "mock_t", "kind": "answers", "model_alias": "qwen3-8b",
                          "model_id": "Qwen/Qwen3-8B", "revision": "", "mock": True})
        (session,) = stored["sessions"]
        self.assertEqual(session["blocks"], [1])
        self.assertEqual(session["limit"], 3)
        self.assertEqual(session["settings"], SETTINGS)
        self.assertEqual(session["summary"], {"planned": 3, "already_done": 0, "called": 3, "errors": 0})
        for field in ("started_utc", "git_commit", "dirty"):
            self.assertIn(field, session)

    def test_resume_skips_done_and_retries_errors(self):
        self.mock_run(limit=5)
        path = self.tmp / "raw/mock_t/answers.jsonl"
        recs = read_jsonl(path)
        # append an error record for the first key, then run again
        append_jsonl(path, dict(recs[0], error="ClientError: boom", text=None))
        again = self.mock_run(limit=5)
        self.assertEqual((again["already_done"], again["called"]), (4, 1))
        self.assertEqual(done_keys(path), {r["key"] for r in recs})
        stored = json.loads((self.tmp / "raw/mock_t/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(stored["sessions"]), 2)

    def test_batch_reused_with_other_model_refused(self):
        self.mock_run(limit=2)
        before = (self.tmp / "raw/mock_t/answers.jsonl").read_text(encoding="utf-8")
        with self.assertRaisesRegex(RunRefused, "model_alias"):
            self.mock_run(model="gemma-3-12b-it", limit=2)
        self.assertEqual((self.tmp / "raw/mock_t/answers.jsonl").read_text(encoding="utf-8"), before)

    def test_refuses_when_build_runs_reports_problems(self):
        with mock.patch("pipeline.run_models.build_runs", return_value=([], [], [], ["the prompts are broken"])):
            with self.assertRaisesRegex(RunRefused, "the prompts are broken"):
                self.mock_run()
        self.assertFalse((self.tmp / "raw").exists())

    def test_mock_labelling_guards(self):
        # A mock client must not write unlabelled records, nor a real client records labelled as mock.
        with self.assertRaisesRegex(RunRefused, "mock"):
            run_answers("mock_t", "qwen3-8b", MockClient("answers"), self.tmp, blocks=[1], limit=1, mock=False)
        with self.assertRaisesRegex(RunRefused, "mock"):
            run_answers("mock_t", "qwen3-8b", CountingClient(), self.tmp, blocks=[1], limit=1, mock=True)
        # A mock batch name must start with "mock".
        with self.assertRaisesRegex(RunRefused, "mock"):
            run_answers("pilot1", "qwen3-8b", MockClient("answers"), self.tmp, blocks=[1], limit=1, mock=True)
        self.assertFalse((self.tmp / "raw").exists())

    # --- the command line

    def test_cli_refuses_real_run_without_flag_and_writes_nothing(self):
        with mock.patch.object(OpenAICompatibleClient, "served_models", side_effect=AssertionError("network")):
            code, _, err = run_cli(["--batch", "pilot1", "--model", "qwen3-8b", "--base-url",
                                    "http://127.0.0.1:9/v1", "--data-root", str(self.tmp)])
        self.assertEqual(code, 2)
        self.assertIn("refusing: ", err)
        self.assertFalse((self.tmp / "raw/pilot1").exists())

    def test_cli_mock_run(self):
        code, out, _ = run_cli(["--batch", "mock_cli", "--model", "qwen3-8b", "--block", "1", "--limit", "3",
                                "--mock", "--data-root", str(self.tmp)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["called"], 3)
        self.assertEqual(len(read_jsonl(self.tmp / "raw/mock_cli/answers.jsonl")), 3)

    def test_cli_unknown_model_and_bad_mock_batch(self):
        self.assertEqual(run_cli(["--batch", "mock_cli", "--model", "nope", "--mock", "--data-root",
                                  str(self.tmp)])[0], 2)
        self.assertEqual(run_cli(["--batch", "pilot1", "--model", "qwen3-8b", "--mock", "--data-root",
                                  str(self.tmp)])[0], 2)
        self.assertFalse((self.tmp / "raw").exists())


if __name__ == "__main__":
    unittest.main()
