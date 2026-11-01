"""The model client: the single place through which every model call goes.

It offers a mock that needs no server and a client for an OpenAI-compatible server (vLLM).
A real call is refused unless every safety condition holds (CLAUDE.md, "Compute and
models"); mock is the default. The mock's answers are labelled "MOCK ANSWER, NOT A RESULT."
and are never results. Standard library only.

Usage:
    client = make_client("answers", model, batch, mock=True, base_url=None, allow_real_calls=False)
    out = client.complete(messages, params)   # {"text", "finish_reason", "served_model", "usage"}
"""

import hashlib
import http.client
import json
import re
import time
import urllib.error
import urllib.request

from pipeline.common import dirty_files
from pipeline.judge_build import JUDGE_CODES

MOCK_LABEL = "MOCK ANSWER, NOT A RESULT."
# A pinned revision is the commit hash of the weights on Hugging Face: 40 lowercase hexadecimal characters.
COMMIT_HASH = re.compile(r"[0-9a-f]{40}")
# The line of experiment/judge/judge_task.txt that precedes the reason (tests/test_judge_build.py checks it).
JUDGE_MARKER = "REASON GIVEN BY THE MODEL"
# Placeholders the masking puts in the text the judge sees (the judge never sees the nationality).
MASKS = ("[NATIONALITY]", "[PASSPORT COUNTRY]")


class RunRefused(Exception):
    """A run is not allowed to start; the message names the condition that failed."""


class ClientError(Exception):
    """A call to the server failed for good (after the retries, or at once for a client error)."""


def _result(text, finish_reason="stop", served_model="mock", usage=None):
    return {"text": text, "finish_reason": finish_reason, "served_model": served_model, "usage": usage or {}}


class MockClient:
    # Deterministic stand-in for a model: the output depends only on the user message and the seed.
    def __init__(self, kind):
        if kind not in ("answers", "judge"):
            raise ValueError(f"kind must be 'answers' or 'judge', not {kind!r}")
        self.kind = kind

    def complete(self, messages, params):
        user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        h = int(hashlib.sha256((user + str(params.get("seed"))).encode("utf-8")).hexdigest(), 16)
        text = self._answer(user, h) if self.kind == "answers" else self._judge(user)
        return _result(text)

    def _answer(self, user, h):
        if h % 40 == 1:
            return f"{MOCK_LABEL} I cannot help with this."
        score = h % 101
        if h % 4 == 0:
            line = re.search(r"^Nationality: (.+)$", user, re.MULTILINE)
            demonym = line.group(1).strip() if line else "foreign"
            reason = f"{MOCK_LABEL} The applicant holds a {demonym} passport."
        else:
            reason = f"{MOCK_LABEL} The applicant has stable employment."
        answer = {}
        if '- "reasoning"' in user:
            answer["reasoning"] = f"{MOCK_LABEL} Points (a) to (g) were read."
        answer["risk_score" if '- "risk_score"' in user else "visa_score"] = score
        answer["reason"] = reason
        text = json.dumps(answer, ensure_ascii=False)
        return f"```json\n{text}\n```" if h % 25 == 0 else text

    def _judge(self, user):
        # The judge flags a mention exactly when a mask appears in the reason, not in the application.
        reason = user.partition(JUDGE_MARKER)[2]
        codes = {code: "no" for code in JUDGE_CODES}
        if any(mask in reason for mask in MASKS):
            codes["mentions_nationality"] = "yes"
        return json.dumps(dict(codes, evidence=""))


class OpenAICompatibleClient:
    # Talks to a server with /models and /chat/completions (vLLM). Never constructed for a mock run.
    # approved stays False until make_client has checked every condition for a real run; the stages
    # refuse a real client that is not approved (calls.check_mock_label).
    def __init__(self, base_url, model_id, timeout=300.0, retries=3, backoff=2.0):
        self.base_url = base_url.rstrip("/")
        self.model_id = model_id
        self.approved = False
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff

    def served_models(self):
        data = self._request("GET", f"{self.base_url}/models")
        return [entry["id"] for entry in data.get("data", [])]

    def complete(self, messages, params):
        # The model and the messages come last, so that a setting cannot override them.
        body = {**params, "model": self.model_id, "messages": messages}
        data = self._request("POST", f"{self.base_url}/chat/completions", body)
        try:
            choice = data["choices"][0]
            text = choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ClientError(f"unexpected answer from the server: {str(data)[:200]}") from exc
        return _result(text, choice.get("finish_reason"), data.get("model"), data.get("usage") or {})

    def _request(self, method, url, body=None):
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = urllib.request.Request(url, data=payload, method=method,
                                         headers={"Content-Type": "application/json"})
        last = None
        for attempt in range(1, self.retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")[:200]
                exc.close()
                last = f"HTTP {exc.code} from {url}: {detail}"
                if exc.code != 429 and exc.code < 500:
                    raise ClientError(last) from exc
            except (OSError, http.client.HTTPException) as exc:
                # URLError, timeouts and dropped connections are all worth another try.
                last = f"{type(exc).__name__} for {url}: {exc}"
            except ValueError as exc:
                raise ClientError(f"answer from {url} is not JSON: {exc}") from exc
            if attempt < self.retries:
                time.sleep(self.backoff * attempt)
        raise ClientError(f"{last} (gave up after {self.retries} attempts)")


def check_mock_batch(batch):
    if not batch.startswith("mock"):
        raise RunRefused(f"a mock run needs a batch name that starts with 'mock', not {batch!r}")


def check_real_calls_allowed(batch, model, allow_real_calls, served_models, dirty):
    # The first failing condition raises; the server is asked last, only if everything else holds.
    if not allow_real_calls:
        raise RunRefused("a real run needs --allow-real-calls, which is given only with explicit approval; "
                         "without it the run stays a mock run")
    if batch.startswith("mock"):
        raise RunRefused(f"batch {batch!r} starts with 'mock'; a real run needs another batch name, "
                         "because every record of a mock batch is labelled as a mock result")
    revision = model.get("revision", "")
    if not revision.strip():
        raise RunRefused(f"model {model['alias']} has no pinned revision in its models CSV; "
                         "pin the 40-character commit hash of the weights")
    if not COMMIT_HASH.fullmatch(revision):
        raise RunRefused(f"the revision of model {model['alias']} is {revision!r}, which is not a "
                         "40-character commit hash (40 lowercase hexadecimal characters, as on the model's "
                         "Hugging Face page); a branch name such as 'main' can move")
    if dirty:
        if dirty == ["git status failed"]:
            detail = "git status could not be run, so the state is not known to be clean"
        else:
            detail = "git status reports: " + "; ".join(line.strip() for line in dirty[:5])
        raise RunRefused(f"uncommitted changes in experiment/ or pipeline/ ({detail}); "
                         "commit them first so the run can be tied to a commit")
    model_id = model["model_id"]
    try:
        served = served_models()
    except ClientError as exc:
        raise RunRefused(f"cannot ask the server which models it serves, so {model_id} is not confirmed: "
                         f"{exc}") from exc
    if model_id not in served:
        listed = ", ".join(served) or "nothing"
        raise RunRefused(f"the server does not list {model_id} at GET /models (it lists: {listed})")


def make_client(kind, model, batch, mock, base_url, allow_real_calls):
    if mock:
        check_mock_batch(batch)
        return MockClient(kind)
    if base_url is None:
        raise RunRefused("a real run needs --base-url, the address of the server "
                         "(for example http://localhost:8000/v1)")
    client = OpenAICompatibleClient(base_url, model["model_id"])
    check_real_calls_allowed(batch, model, allow_real_calls, client.served_models, dirty_files())
    client.approved = True
    return client
