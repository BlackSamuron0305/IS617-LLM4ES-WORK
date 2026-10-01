"""OpenAI-compatible chat endpoint (vLLM on bwUniCluster). Standard library only.

vLLM specifics:
* ``chat_template_kwargs`` (e.g. ``{"enable_thinking": false}`` for Qwen3) is sent
  as a top-level request field via the model's ``extra_body``;
* ``response_format: {"type": "json_object"}`` enables JSON mode;
* ``seed`` gives per-request reproducible sampling;
* ``logprobs`` / ``top_logprobs`` return token log-probabilities.
"""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request

from ..config import ModelSpec
from .base import (ChatRequest, ChatResponse, NonRetryableProviderError, Provider, RetryableProviderError,
                   RETRYABLE_STATUS, trim_logprobs)


def build_payload(spec: ModelSpec, req: ChatRequest) -> dict:
    payload: dict = {
        "model": spec.model_id,
        "messages": req.messages,
        "temperature": req.temperature,
        "max_tokens": req.max_tokens,
    }
    if req.top_p is not None and spec.send_top_p:
        payload["top_p"] = req.top_p
    if req.seed is not None and spec.supports_seed:
        payload["seed"] = req.seed
    if req.json_mode and spec.supports_json_mode:
        payload["response_format"] = {"type": "json_object"}
    if req.want_logprobs and spec.supports_logprobs:
        payload["logprobs"] = True
        payload["top_logprobs"] = req.top_logprobs
    for k, v in (req.extra_params or {}).items():
        payload[k] = v
    for k, v in (spec.extra_body or {}).items():
        payload[k] = v
    return payload


class OpenAICompatibleProvider(Provider):
    name = "openai_compatible"

    def __init__(self, spec: ModelSpec):
        super().__init__(spec)
        self._base_url: str | None = None
        self._api_key: str | None = None

    def check_ready(self) -> None:
        self._base_url = self._env(self.spec.base_url_env or "VLLM_BASE_URL", required=True).rstrip("/")
        self._api_key = self._env(self.spec.api_key_env, required=False)

    def _get_json(self, url: str) -> dict | None:
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:  # introspection is best effort
            return None

    def introspect(self) -> dict:
        """Ask the vLLM server what it serves (/v1/models) and its version (/version)."""
        if self._base_url is None:
            self.check_ready()
        models = self._get_json(f"{self._base_url}/models")
        root = self._base_url[:-3] if self._base_url.endswith("/v1") else self._base_url
        version = self._get_json(f"{root}/version")
        served = None
        if models and isinstance(models.get("data"), list):
            served = [{k: m.get(k) for k in ("id", "root", "max_model_len", "owned_by")} for m in models["data"]]
        return {"endpoint": self._base_url, "served_models": served,
                "server_version": (version or {}).get("version")}

    def complete(self, request: ChatRequest) -> ChatResponse:
        if self._base_url is None:
            self.check_ready()
        payload = build_payload(self.spec, request)
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        url = f"{self._base_url}/chat/completions"
        t0 = time.perf_counter()
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=self.spec.timeout_s) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")[:1000]
            msg = f"HTTP {e.code} from {url}: {detail}"
            if e.code in RETRYABLE_STATUS or e.code >= 500:
                raise RetryableProviderError(msg, status_code=e.code) from e
            raise NonRetryableProviderError(msg, status_code=e.code) from e
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
            raise RetryableProviderError(f"connection problem with {url}: {e}") from e
        except json.JSONDecodeError as e:
            raise RetryableProviderError(f"non-JSON response from {url}: {e}") from e
        latency = (time.perf_counter() - t0) * 1000.0
        try:
            choice = body["choices"][0]
            text = choice["message"].get("content")
            finish = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError) as e:
            raise NonRetryableProviderError(f"unexpected response shape: {str(body)[:500]}") from e
        lp = None
        if choice.get("logprobs"):
            lp = trim_logprobs(choice["logprobs"].get("content"), request.logprobs_max_tokens)
        params = {k: v for k, v in payload.items() if k != "messages"}
        return ChatResponse(
            text=text,
            finish_reason=finish,
            usage=body.get("usage"),
            latency_ms=round(latency, 1),
            logprobs=lp,
            raw_metadata={"id": body.get("id"), "served_model": body.get("model"),
                          "system_fingerprint": body.get("system_fingerprint"), "endpoint": self._base_url},
            request_params=params,
        )


