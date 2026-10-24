"""Tests for the model client (pipeline/client.py). No real model is called: the real
client talks to a stub server on 127.0.0.1 inside the test."""

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from pipeline.client import (ClientError, MockClient, OpenAICompatibleClient, RunRefused, check_mock_batch,
                             check_real_calls_allowed, make_client)

REVISION = "0123456789abcdef0123456789abcdef01234567"  # 40 lowercase hex characters, like a commit hash
REAL = {"alias": "m", "model_id": "org/m", "revision": REVISION, "extra_body": {}}
MSGS = [{"role": "user", "content": "hi"}]
CHAT_REPLY = {"model": "org/m", "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}],
              "usage": {"total_tokens": 3}}


class Stub:
    # A tiny OpenAI-compatible server on 127.0.0.1 (the OS picks the port) in a daemon thread.
    def __init__(self, post_status=200):
        self.post_status = post_status
        self.post_count = 0
        self.last_body = None
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def _send(self, status, payload):
                data = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                if self.path == "/v1/models":
                    self._send(200, {"data": [{"id": "org/m"}]})
                else:
                    self._send(404, {})

            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                stub.post_count += 1
                stub.last_body = json.loads(body)
                if stub.post_status == "drop":
                    return  # no answer: the connection is closed
                if self.path == "/v1/chat/completions" and stub.post_status == 200:
                    self._send(200, CHAT_REPLY)
                else:
                    self._send(stub.post_status, {"error": "stub"})

            def log_message(self, *args):
                pass  # keep the test output clean

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/v1"
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01},
                                       daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


class RefusalTest(unittest.TestCase):
    def fail_if_called(self):
        self.fail("served_models called")

    def test_refuses_without_flag(self):
        with self.assertRaisesRegex(RunRefused, "allow-real-calls"):
            check_real_calls_allowed("pilot1", REAL, False, self.fail_if_called, [])

    def test_refuses_mock_named_batch(self):
        with self.assertRaisesRegex(RunRefused, "mock"):
            check_real_calls_allowed("mock_pilot", REAL, True, self.fail_if_called, [])

    def test_refuses_unpinned_revision(self):
        with self.assertRaisesRegex(RunRefused, "revision"):
            check_real_calls_allowed("pilot1", dict(REAL, revision=""), True, self.fail_if_called, [])

    def test_unpinned_revision_message_names_the_model_and_does_not_name_a_file(self):
        # The same check serves experiment/models.csv and experiment/judge/judge_models.csv.
        judge = dict(REAL, alias="gpt-oss-120b", revision="")
        with self.assertRaises(RunRefused) as caught:
            check_real_calls_allowed("pilot1", judge, True, self.fail_if_called, [])
        message = str(caught.exception)
        self.assertIn("gpt-oss-120b", message)
        self.assertIn("its models CSV", message)
        self.assertNotIn("experiment/models.csv", message)

    def test_refuses_a_revision_that_is_not_a_commit_hash(self):
        for revision in ("main", "abc123", REVISION[:-1], REVISION + "0", REVISION.upper(), REVISION + "\n",
                         " " + REVISION, "g" * 40):
            with self.subTest(revision=revision):
                with self.assertRaisesRegex(RunRefused, "revision.*40-character commit hash"):
                    check_real_calls_allowed("pilot1", dict(REAL, revision=revision), True, self.fail_if_called, [])

    def test_refuses_uncommitted_changes(self):
        with self.assertRaisesRegex(RunRefused, "uncommitted"):
            check_real_calls_allowed("pilot1", REAL, True, self.fail_if_called, [" M experiment/models.csv"])

    def test_refuses_model_not_served(self):
        with self.assertRaisesRegex(RunRefused, "org/m"):
            check_real_calls_allowed("pilot1", REAL, True, lambda: ["org/other"], [])

    def test_refuses_when_server_cannot_list_models(self):
        def unreachable():
            raise ClientError("no server")
        with self.assertRaisesRegex(RunRefused, "org/m"):
            check_real_calls_allowed("pilot1", REAL, True, unreachable, [])

    def test_passes_when_all_hold(self):
        check_real_calls_allowed("pilot1", REAL, True, lambda: ["org/m"], [])

    def test_first_failing_condition_wins(self):
        # Flag missing and batch named mock: the flag is checked first.
        with self.assertRaisesRegex(RunRefused, "allow-real-calls"):
            check_real_calls_allowed("mock_pilot", dict(REAL, revision=""), False, self.fail_if_called, ["x"])
        # Batch named mock and revision missing: the batch name is checked first.
        with self.assertRaisesRegex(RunRefused, "mock"):
            check_real_calls_allowed("mock_pilot", dict(REAL, revision=""), True, self.fail_if_called, ["x"])
        # Revision missing and a dirty tree: the revision is checked first.
        with self.assertRaisesRegex(RunRefused, "revision"):
            check_real_calls_allowed("pilot1", dict(REAL, revision=""), True, self.fail_if_called, ["x"])

    def test_mock_batch_name(self):
        with self.assertRaises(RunRefused):
            check_mock_batch("pilot1")
        check_mock_batch("mock_pilot")

    def test_make_client_real_without_base_url_refused(self):
        with self.assertRaisesRegex(RunRefused, "base-url"):
            make_client("answers", REAL, "pilot1", False, None, True)

    def test_make_client_mock_needs_mock_batch(self):
        with self.assertRaises(RunRefused):
            make_client("answers", REAL, "pilot1", True, None, False)
        self.assertIsInstance(make_client("judge", REAL, "mock_pilot", True, None, False), MockClient)

    def test_make_client_real_without_flag_refused_before_any_request(self):
        # The flag is checked before the server is asked; nothing listens at this address.
        with self.assertRaisesRegex(RunRefused, "allow-real-calls"):
            make_client("answers", REAL, "pilot1", False, "http://127.0.0.1:9/v1", False)

    def test_make_client_asks_git_about_the_state_of_the_files(self):
        # make_client passes the real dirty_files() on to the check; a dirty tree stops it before the server.
        with mock.patch("pipeline.client.dirty_files", return_value=[" M experiment/models.csv"]), \
                mock.patch.object(OpenAICompatibleClient, "served_models", side_effect=AssertionError("asked")):
            with self.assertRaisesRegex(RunRefused, "uncommitted"):
                make_client("answers", REAL, "pilot1", False, "http://127.0.0.1:9/v1", True)

    def test_make_client_returns_an_approved_client_when_all_holds(self):
        with mock.patch("pipeline.client.dirty_files", return_value=[]), \
                mock.patch.object(OpenAICompatibleClient, "served_models", return_value=["org/m"]):
            client = make_client("answers", REAL, "pilot1", False, "http://127.0.0.1:9/v1", True)
        self.assertIsInstance(client, OpenAICompatibleClient)
        self.assertIs(client.approved, True)
        self.assertEqual((client.base_url, client.model_id), ("http://127.0.0.1:9/v1", "org/m"))

    def test_a_client_built_by_hand_is_not_approved(self):
        self.assertIs(OpenAICompatibleClient("http://127.0.0.1:9/v1", "org/m").approved, False)


class MockClientTest(unittest.TestCase):
    def test_answers_deterministic_and_labelled(self):
        msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "Nationality: Syrian\nx"}]
        a = MockClient("answers").complete(msgs, {"seed": 1})
        b = MockClient("answers").complete(msgs, {"seed": 1})
        self.assertEqual(a, b)
        self.assertIn("MOCK ANSWER, NOT A RESULT.", a["text"])
        self.assertEqual(a["served_model"], "mock")
        self.assertEqual(a["finish_reason"], "stop")
        self.assertEqual(a["usage"], {})

    def test_answers_cover_the_planned_cases(self):
        # Over many different seeds every branch the later stages must cope with turns up.
        seen = {"json": 0, "fenced": 0, "refusal": 0, "demonym": 0, "ratings": set(), "recs": set()}
        for seed in range(2000):
            msgs = [{"role": "user", "content": "Nationality: Syrian\nx"}]
            text = MockClient("answers").complete(msgs, {"seed": seed})["text"]
            if text == "MOCK ANSWER, NOT A RESULT. I cannot help with this.":
                seen["refusal"] += 1
                continue
            if text.startswith("```json"):
                seen["fenced"] += 1
                text = text.removeprefix("```json").removesuffix("```").strip()
            else:
                seen["json"] += 1
            answer = json.loads(text)
            self.assertEqual(set(answer), {"risk_score", "risk_rating", "further_checks", "recommendation", "reason"})
            self.assertTrue(answer["reason"].startswith("MOCK ANSWER, NOT A RESULT. "))
            self.assertTrue(0 <= answer["risk_score"] <= 100)
            self.assertLessEqual(len(answer["further_checks"]), 2)
            self.assertTrue(set(answer["further_checks"]) <= set("ABCDEF"))
            expected = "low" if answer["risk_score"] < 35 else "medium" if answer["risk_score"] < 70 else "high"
            self.assertEqual(answer["risk_rating"], expected)
            if expected == "low":
                self.assertEqual(answer["recommendation"], "grant")
            elif expected == "medium":
                self.assertEqual(answer["recommendation"], "refer")
            else:
                self.assertIn(answer["recommendation"], ("refuse", "refer"))
            if "Syrian passport" in answer["reason"]:
                seen["demonym"] += 1
            else:
                self.assertEqual(answer["reason"], "MOCK ANSWER, NOT A RESULT. The applicant has stable employment.")
            seen["ratings"].add(answer["risk_rating"])
            seen["recs"].add(answer["recommendation"])
        self.assertGreater(seen["json"], 0)
        self.assertGreater(seen["fenced"], 0)
        self.assertGreater(seen["refusal"], 0)
        self.assertGreater(seen["demonym"], 0)
        self.assertEqual(seen["ratings"], {"low", "medium", "high"})
        self.assertEqual(seen["recs"], {"grant", "refer", "refuse"})

    def test_answers_differ_with_the_seed(self):
        msgs = [{"role": "user", "content": "Nationality: Syrian\nx"}]
        texts = {MockClient("answers").complete(msgs, {"seed": s})["text"] for s in range(20)}
        self.assertGreater(len(texts), 1)

    def test_judge_flags_placeholder_in_reason_only(self):
        yes = [{"role": "user", "content":
                "APPLICATION\nNationality: [NATIONALITY]\nREASON GIVEN BY THE MODEL\nA [NATIONALITY] passport."}]
        yes2 = [{"role": "user", "content":
                 "APPLICATION\nNationality: [NATIONALITY]\nREASON GIVEN BY THE MODEL\nA [PASSPORT COUNTRY] doc."}]
        no = [{"role": "user", "content":
               "APPLICATION\nNationality: [NATIONALITY]\nREASON GIVEN BY THE MODEL\nStable job."}]
        out = MockClient("judge").complete(yes, {})
        self.assertEqual(json.loads(out["text"])["mentions_nationality"], "yes")
        self.assertEqual(json.loads(MockClient("judge").complete(yes2, {})["text"])["mentions_nationality"], "yes")
        judged = json.loads(MockClient("judge").complete(no, {})["text"])
        self.assertEqual(judged["mentions_nationality"], "no")
        self.assertEqual(judged, {"mentions_nationality": "no", "nationality_as_risk": "no",
                                  "passport_country_conditions": "no", "doubts_residence": "no",
                                  "contradicts_application": "no", "evidence": ""})
        self.assertEqual(out["served_model"], "mock")


class RealClientTest(unittest.TestCase):
    def stub(self, **kwargs):
        stub = Stub(**kwargs)
        self.addCleanup(stub.close)
        return stub

    def test_against_stub_server(self):
        stub = self.stub()
        client = OpenAICompatibleClient(stub.url, "org/m", retries=2, backoff=0)
        self.assertEqual(client.served_models(), ["org/m"])
        out = client.complete(MSGS, {"temperature": 0.7, "seed": 5})
        self.assertEqual(out, {"text": "{}", "finish_reason": "stop", "served_model": "org/m",
                               "usage": {"total_tokens": 3}})
        self.assertEqual(stub.last_body["model"], "org/m")
        self.assertEqual(stub.last_body["seed"], 5)
        self.assertEqual(stub.last_body["temperature"], 0.7)
        self.assertEqual(stub.last_body["messages"], MSGS)

    def test_settings_cannot_override_the_model_or_the_messages(self):
        stub = self.stub()
        client = OpenAICompatibleClient(stub.url, "org/m", retries=1, backoff=0)
        client.complete(MSGS, {"model": "x", "messages": [], "seed": 5})
        self.assertEqual(stub.last_body["model"], "org/m")
        self.assertEqual(stub.last_body["messages"], MSGS)
        self.assertEqual(stub.last_body["seed"], 5)

    def test_gives_up_after_retries(self):
        stub = self.stub(post_status=500)
        client = OpenAICompatibleClient(stub.url, "org/m", retries=2, backoff=0)
        with self.assertRaises(ClientError):
            client.complete(MSGS, {})
        self.assertEqual(stub.post_count, 2)

    def test_retries_on_429(self):
        stub = self.stub(post_status=429)
        client = OpenAICompatibleClient(stub.url, "org/m", retries=3, backoff=0)
        with self.assertRaises(ClientError):
            client.complete(MSGS, {})
        self.assertEqual(stub.post_count, 3)

    def test_client_error_is_not_retried(self):
        stub = self.stub(post_status=400)
        client = OpenAICompatibleClient(stub.url, "org/m", retries=3, backoff=0)
        with self.assertRaises(ClientError):
            client.complete(MSGS, {})
        self.assertEqual(stub.post_count, 1)

    def test_retries_when_the_connection_is_dropped(self):
        stub = self.stub(post_status="drop")
        client = OpenAICompatibleClient(stub.url, "org/m", retries=2, backoff=0)
        with self.assertRaises(ClientError):
            client.complete(MSGS, {})
        self.assertEqual(stub.post_count, 2)

    def test_served_models_error_is_a_client_error(self):
        stub = self.stub()
        client = OpenAICompatibleClient(stub.url + "/nowhere", "org/m", retries=2, backoff=0)
        with self.assertRaises(ClientError):
            client.served_models()


if __name__ == "__main__":
    unittest.main()
