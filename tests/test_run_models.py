"""Tests for the run settings, the call loop and the run_models stage. No real model is
called: every run uses the mock client or a client defined in the test."""

import contextlib
import io
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from pipeline.build_runs import build_runs
from pipeline.calls import (begin_stage, check_mock_label, done_keys, record_summary, request_params, run_calls,
                            update_manifest)
from pipeline.client import ClientError, MockClient, OpenAICompatibleClient, RunRefused, make_client
from pipeline.common import EXPERIMENT, append_jsonl, load_models, load_settings, read_jsonl
from pipeline.run_models import main, plan_items, run_answers
from tests.test_client import REVISION, Stub

# Fixed settings for the tests of the call loop; the values in experiment/run_settings.csv may change.
SETTINGS = {"temperature": 0.7, "top_p": 1.0, "max_tokens": 400, "seed": "per_call", "json_schema": False}
SETTINGS_CSV = ("setting,answers,judge,status,note\n"
                "temperature,0.7,0,provisional,\n"
                "top_p,1,1,provisional,\n"
                "max_tokens,400,1000,provisional,\n"
                "seed,per_call,0,provisional,\n"
                "json_schema,{answers_schema},no,open,\n")
MSGS = [{"role": "user", "content": "hi"}]
# The model the tests run, as the live experiment/models.csv has it.
MODEL = load_models(EXPERIMENT / "models.csv")["qwen3-32b"]


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

    def mock_run(self, batch="mock_t", model="qwen3-32b", limit=5, **kwargs):
        return run_answers(batch, model, MockClient("answers"), self.tmp, blocks=[1], limit=limit, mock=True, **kwargs)

    # --- settings and request parameters

    def settings_file(self, answers_schema="no"):
        path = self.tmp / "s.csv"
        path.write_text(SETTINGS_CSV.format(answers_schema=answers_schema), encoding="utf-8", newline="\n")
        return path

    def test_load_settings(self):
        # Read from a file of the test's own: the values in experiment/run_settings.csv may change.
        path = self.settings_file()
        self.assertEqual(load_settings("judge", path), {"temperature": 0.0, "top_p": 1.0, "max_tokens": 1000,
                                                        "seed": 0, "json_schema": False})
        self.assertEqual(load_settings("answers", path), SETTINGS)
        self.assertIs(load_settings("answers", self.settings_file("yes"))["json_schema"], True)

    def test_load_settings_reads_the_live_file(self):
        for kind in ("answers", "judge"):
            settings = load_settings(kind)
            self.assertEqual(set(settings), {"temperature", "top_p", "max_tokens", "seed", "json_schema"})
            self.assertIsInstance(settings["json_schema"], bool)

    def test_load_settings_rejects_bad_kind_and_value(self):
        with self.assertRaises(ValueError):
            load_settings("other")
        with self.assertRaisesRegex(ValueError, "json_schema"):
            load_settings("answers", self.settings_file("maybe"))

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

    def test_shards_are_disjoint_and_complete(self):
        runs = build_runs()[0]
        whole = [i["key"] for i in plan_items(runs, [1], None)]
        parts = [[i["key"] for i in plan_items(runs, [1], None, shard=(k, 4))] for k in range(4)]
        self.assertEqual(sorted(sum(parts, [])), sorted(whole))
        self.assertEqual(len({k for part in parts for k in part}), len(whole))

    def test_remaining_counts_without_a_server(self):
        from pipeline.run_models import count_remaining, parse_shard
        with tempfile.TemporaryDirectory() as tmp:
            first = count_remaining("mock_r", tmp, [1], wordings=[1], max_repetitions=1)
            self.assertEqual(first, {"planned": 520, "remaining": 520})
            run_answers("mock_r", "qwen3-32b", MockClient("answers"), Path(tmp), blocks=[1], limit=20, mock=True,
                        wordings=[1], max_repetitions=1)
            self.assertEqual(count_remaining("mock_r", tmp, [1], wordings=[1], max_repetitions=1)["remaining"], 500)
        self.assertEqual(parse_shard("2/5"), (2, 5))
        self.assertIsNone(parse_shard(None))
        with self.assertRaises(ValueError):
            parse_shard("5/5")

    def test_plan_items_pilot_filters(self):
        # The pilot: block 1, wording 1, one repetition = 20 applicants x 26 nationalities.
        runs = build_runs("all")[0]
        pilot = plan_items(runs, [1], None, ["base"], [1], 1)
        self.assertEqual(len(pilot), 520)
        self.assertEqual({i["meta"]["repetition"] for i in pilot}, {1})
        self.assertEqual({i["meta"]["block"] for i in pilot}, {1})
        self.assertTrue(all(i["key"].endswith("__w1__r1") for i in pilot))
        # Without the filters block 1 is five repetitions of three wordings.
        self.assertEqual(len(plan_items(runs, [1], None, ["base"])), 7800)
        self.assertEqual(len(plan_items(runs, [4], None, ["no_guidance"], [2, 3], 5)), 1040)

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

    def test_manifest_is_written_through_a_temp_file_that_is_gone_afterwards(self):
        path = self.tmp / "b" / "manifest.json"
        header = {"batch": "mock_t", "model_alias": "m1", "mock": True}
        update_manifest(path, header, {"started_utc": "t1"})
        record_summary(path, {"called": 1})
        self.assertEqual([p.name for p in path.parent.iterdir()], ["manifest.json"])

    def test_failed_manifest_write_keeps_the_old_manifest(self):
        path = self.tmp / "b" / "manifest.json"
        header = {"batch": "mock_t", "model_alias": "m1", "mock": True}
        update_manifest(path, header, {"started_utc": "t1"})
        before = path.read_bytes()
        with mock.patch("pipeline.calls.os.replace", side_effect=OSError("disk")):
            with self.assertRaises(OSError):
                update_manifest(path, header, {"started_utc": "t2"})
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual([p.name for p in path.parent.iterdir()], ["manifest.json"])

    # --- run_answers

    def test_mock_run_writes_labelled_records(self):
        summary = self.mock_run(limit=30)
        self.assertEqual(summary["called"], 30)
        recs = read_jsonl(self.tmp / "raw/mock_t/answers.jsonl")
        self.assertEqual(len(recs), 30)
        self.assertTrue(all(r["mock"] for r in recs))
        self.assertTrue(all(r["kind"] == "answers" and r["model_alias"] == "qwen3-32b" and r["batch"] == "mock_t"
                            for r in recs))
        self.assertTrue(all(r["error"] is None and r["text"] for r in recs))
        # The model's extra_body from models.csv goes into the request.
        self.assertEqual({key: recs[0]["params"][key] for key in MODEL["extra_body"]}, MODEL["extra_body"])

    def test_manifest_has_header_and_session_with_summary(self):
        self.mock_run(limit=3)
        stored = json.loads((self.tmp / "raw/mock_t/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual({k: stored[k] for k in ("batch", "kind", "model_alias", "model_id", "revision", "mock")},
                         {"batch": "mock_t", "kind": "answers", "model_alias": "qwen3-32b",
                          "model_id": MODEL["model_id"], "revision": MODEL["revision"], "mock": True})
        (session,) = stored["sessions"]
        self.assertEqual(session["blocks"], [1])
        self.assertEqual(session["limit"], 3)
        self.assertEqual(session["settings"], load_settings("answers"))
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

    def test_resume_over_a_torn_last_line_calls_that_key_again(self):
        # A killed job can leave half a record at the end of the raw file.
        self.mock_run(limit=5)
        path = self.tmp / "raw/mock_t/answers.jsonl"
        keys = {r["key"] for r in read_jsonl(path)}
        data = path.read_bytes()
        last_start = data.rstrip(b"\n").rfind(b"\n") + 1
        path.write_bytes(data[:last_start + 25])
        with contextlib.redirect_stderr(io.StringIO()) as err:
            again = self.mock_run(limit=5)
            self.assertEqual((again["already_done"], again["called"]), (4, 1))
            self.assertEqual(done_keys(path), keys)
        self.assertIn("skipped 1 unreadable line(s)", err.getvalue())
        self.assertEqual(len(path.read_bytes().splitlines()), 6)  # 4 whole records, the fragment, the new record

    def test_batch_reused_with_other_model_refused(self):
        self.mock_run(limit=2)
        before = (self.tmp / "raw/mock_t/answers.jsonl").read_text(encoding="utf-8")
        with self.assertRaisesRegex(RunRefused, "model_alias"):
            self.mock_run(model="gemma-4-31b-it", limit=2)
        self.assertEqual((self.tmp / "raw/mock_t/answers.jsonl").read_text(encoding="utf-8"), before)

    def test_refuses_when_build_runs_reports_problems(self):
        with mock.patch("pipeline.run_models.build_runs", return_value=([], [], [], ["the prompts are broken"])):
            with self.assertRaisesRegex(RunRefused, "the prompts are broken"):
                self.mock_run()
        self.assertFalse((self.tmp / "raw").exists())

    def test_mock_labelling_guards(self):
        # A mock client must not write unlabelled records, nor a real client records labelled as mock.
        with self.assertRaisesRegex(RunRefused, "mock"):
            run_answers("mock_t", "qwen3-32b", MockClient("answers"), self.tmp, blocks=[1], limit=1, mock=False)
        with self.assertRaisesRegex(RunRefused, "mock"):
            run_answers("mock_t", "qwen3-32b", CountingClient(), self.tmp, blocks=[1], limit=1, mock=True)
        # A mock batch name must start with "mock".
        with self.assertRaisesRegex(RunRefused, "mock"):
            run_answers("pilot1", "qwen3-32b", MockClient("answers"), self.tmp, blocks=[1], limit=1, mock=True)
        self.assertFalse((self.tmp / "raw").exists())

    # --- the gate: only make_client can produce a client that may make real calls

    def test_a_real_client_built_by_hand_is_refused_and_nothing_is_written(self):
        client = OpenAICompatibleClient("http://127.0.0.1:9/v1", MODEL["model_id"])
        with mock.patch.object(OpenAICompatibleClient, "complete", side_effect=AssertionError("called")):
            with self.assertRaisesRegex(RunRefused, "make_client"):
                run_answers("pilot1", "qwen3-32b", client, self.tmp, blocks=[1], limit=1, mock=False)
        self.assertFalse((self.tmp / "raw").exists())

    def test_an_approved_client_passes_the_label_check(self):
        client = OpenAICompatibleClient("http://127.0.0.1:9/v1", MODEL["model_id"])
        client.approved = True  # what make_client does once every condition holds
        check_mock_label(client, False, "pilot1")

    def test_any_other_non_mock_client_is_refused_too(self):
        with self.assertRaisesRegex(RunRefused, "make_client"):
            check_mock_label(CountingClient(), False, "pilot1")

    # --- what the manifest records about the server

    def test_real_session_records_the_server_facts_from_the_environment(self):
        client = OpenAICompatibleClient("http://127.0.0.1:9/v1", MODEL["model_id"])
        client.approved = True
        path = self.tmp / "manifest.json"
        with mock.patch.dict(os.environ, {"MODEL_PATH": "/models/qwen3-32b", "VLLM_ARGS": "--max-model-len 8192"}):
            begin_stage(path, "answers", "pilot1", "qwen3-32b", MODEL, False, SETTINGS, {}, client)
        (session,) = json.loads(path.read_text(encoding="utf-8"))["sessions"]
        self.assertEqual((session["model_path"], session["vllm_args"], session["base_url"]),
                         ("/models/qwen3-32b", "--max-model-len 8192", "http://127.0.0.1:9/v1"))

    def test_real_session_records_empty_strings_when_the_environment_is_not_set(self):
        client = OpenAICompatibleClient("http://127.0.0.1:9/v1", MODEL["model_id"])
        client.approved = True
        path = self.tmp / "manifest.json"
        with mock.patch.dict(os.environ):
            os.environ.pop("MODEL_PATH", None)
            os.environ.pop("VLLM_ARGS", None)
            begin_stage(path, "answers", "pilot1", "qwen3-32b", MODEL, False, SETTINGS, {}, client)
        (session,) = json.loads(path.read_text(encoding="utf-8"))["sessions"]
        self.assertEqual((session["model_path"], session["vllm_args"]), ("", ""))

    def test_real_run_through_make_client_against_a_stub_server(self):
        # The whole real path on 127.0.0.1: make_client approves the client, the stage accepts it, the
        # records are not labelled as mock and the session names the server.
        stub = Stub()
        self.addCleanup(stub.close)
        with mock.patch("pipeline.client.dirty_files", return_value=[]),                 mock.patch.dict(os.environ, {"MODEL_PATH": "/models/m", "VLLM_ARGS": "--x"}):
            client = make_client("answers", dict(MODEL, model_id="org/m", revision=REVISION), "pilot1", False,
                                 stub.url, True)
            summary = run_answers("pilot1", "qwen3-32b", client, self.tmp, blocks=[1], limit=2, workers=1)
        self.assertEqual((summary["called"], summary["errors"]), (2, 0))
        records = read_jsonl(self.tmp / "raw/pilot1/answers.jsonl")
        self.assertEqual([r["mock"] for r in records], [False, False])
        self.assertEqual({r["served_model"] for r in records}, {"org/m"})
        (session,) = json.loads((self.tmp / "raw/pilot1/manifest.json").read_text(encoding="utf-8"))["sessions"]
        self.assertEqual((session["model_path"], session["vllm_args"], session["base_url"]),
                         ("/models/m", "--x", stub.url))

    def test_mock_session_records_no_server_facts(self):
        with mock.patch.dict(os.environ, {"MODEL_PATH": "/models/qwen3-32b", "VLLM_ARGS": "--x"}):
            self.mock_run(limit=1)
        stored = json.loads((self.tmp / "raw/mock_t/manifest.json").read_text(encoding="utf-8"))
        (session,) = stored["sessions"]
        self.assertEqual((session["model_path"], session["vllm_args"], session["base_url"]), ("", "", None))

    # --- the command line

    def test_cli_refuses_real_run_without_flag_and_writes_nothing(self):
        with mock.patch.object(OpenAICompatibleClient, "served_models", side_effect=AssertionError("network")):
            code, _, err = run_cli(["--batch", "pilot1", "--model", "qwen3-32b", "--base-url",
                                    "http://127.0.0.1:9/v1", "--data-root", str(self.tmp)])
        self.assertEqual(code, 2)
        self.assertIn("refusing: ", err)
        self.assertFalse((self.tmp / "raw/pilot1").exists())

    def test_cli_mock_run(self):
        code, out, _ = run_cli(["--batch", "mock_cli", "--model", "qwen3-32b", "--block", "1", "--limit", "3",
                                "--mock", "--data-root", str(self.tmp)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["called"], 3)
        self.assertEqual(len(read_jsonl(self.tmp / "raw/mock_cli/answers.jsonl")), 3)

    def test_cli_unknown_model_and_bad_mock_batch(self):
        self.assertEqual(run_cli(["--batch", "mock_cli", "--model", "nope", "--mock", "--data-root",
                                  str(self.tmp)])[0], 2)
        self.assertEqual(run_cli(["--batch", "pilot1", "--model", "qwen3-32b", "--mock", "--data-root",
                                  str(self.tmp)])[0], 2)
        self.assertFalse((self.tmp / "raw").exists())


if __name__ == "__main__":
    unittest.main()
