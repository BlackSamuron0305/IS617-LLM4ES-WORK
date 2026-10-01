"""Optional API providers (OpenAI, Anthropic, Google). SDKs are imported lazily.

None of these is exercised by the test-suite and none may be called without
``--allow-real-calls``. Model ids in config/models.csv are marked
``status: unverified`` and must be pinned before a run.
"""

from __future__ import annotations

import time

from ..config import ModelSpec
from .base import (ChatRequest, ChatResponse, NonRetryableProviderError, Provider,
                   ProviderConfigError, classify_exception, trim_logprobs)


def _import(module: str, extra: str):
    try:
        return __import__(module, fromlist=["_"])
    except ImportError as e:
        raise ProviderConfigError(
            f"package for {module!r} is not installed; install the optional extra: "
            f"pip install -e .[{extra}]"
        ) from e


def _as_dict(obj) -> dict | None:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    for attr in ("model_dump", "to_dict"):
        if hasattr(obj, attr):
            try:
                return getattr(obj, attr)()
            except Exception:  # pragma: no cover - defensive
                pass
    return {k: v for k, v in vars(obj).items() if not k.startswith("_")} if hasattr(obj, "__dict__") else None


class OpenAIProvider(Provider):
    name = "openai"

    def __init__(self, spec: ModelSpec):
        super().__init__(spec)
        self._client = None

    def check_ready(self) -> None:
        openai = _import("openai", "openai")
        key = self._env(self.spec.api_key_env or "OPENAI_API_KEY")
        self._client = openai.OpenAI(api_key=key, timeout=self.spec.timeout_s, max_retries=0)

    def complete(self, request: ChatRequest) -> ChatResponse:
        if self._client is None:
            self.check_ready()
        params: dict = {"model": self.spec.model_id, "temperature": request.temperature,
                        "max_tokens": request.max_tokens}
        if request.top_p is not None and self.spec.send_top_p:
            params["top_p"] = request.top_p
        if request.seed is not None and self.spec.supports_seed:
            params["seed"] = request.seed
        if request.json_mode and self.spec.supports_json_mode:
            params["response_format"] = {"type": "json_object"}
        if request.want_logprobs and self.spec.supports_logprobs:
            params["logprobs"] = True
            params["top_logprobs"] = request.top_logprobs
        if self.spec.extra_body:
            params["extra_body"] = self.spec.extra_body
        t0 = time.perf_counter()
        try:
            resp = self._client.chat.completions.create(messages=request.messages, **params)
        except Exception as e:  # SDK exceptions -> typed provider errors
            raise classify_exception(e) from e
        latency = (time.perf_counter() - t0) * 1000.0
        choice = resp.choices[0]
        lp = None
        if getattr(choice, "logprobs", None) is not None and getattr(choice.logprobs, "content", None):
            lp = trim_logprobs(choice.logprobs.content, request.logprobs_max_tokens)
        return ChatResponse(
            text=choice.message.content, finish_reason=choice.finish_reason, usage=_as_dict(resp.usage),
            latency_ms=round(latency, 1), logprobs=lp,
            raw_metadata={"id": resp.id, "served_model": resp.model,
                          "system_fingerprint": getattr(resp, "system_fingerprint", None)},
            request_params=params,
        )


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, spec: ModelSpec):
        super().__init__(spec)
        self._client = None

    def check_ready(self) -> None:
        anthropic = _import("anthropic", "anthropic")
        key = self._env(self.spec.api_key_env or "ANTHROPIC_API_KEY")
        self._client = anthropic.Anthropic(api_key=key, timeout=self.spec.timeout_s, max_retries=0)

    def complete(self, request: ChatRequest) -> ChatResponse:
        if self._client is None:
            self.check_ready()
        params: dict = {"model": self.spec.model_id, "max_tokens": request.max_tokens,
                        "temperature": request.temperature}
        if request.top_p is not None and self.spec.send_top_p:
            params["top_p"] = request.top_p
        system = request.system_text
        messages = [m for m in request.messages if m["role"] != "system"]
        t0 = time.perf_counter()
        try:
            resp = self._client.messages.create(system=system, messages=messages, **params)
        except Exception as e:
            raise classify_exception(e) from e
        latency = (time.perf_counter() - t0) * 1000.0
        text = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text")
        return ChatResponse(
            text=text, finish_reason=resp.stop_reason, usage=_as_dict(resp.usage),
            latency_ms=round(latency, 1), logprobs=None,
            raw_metadata={"id": resp.id, "served_model": resp.model}, request_params=params,
        )


class GoogleProvider(Provider):
    name = "google"

    def __init__(self, spec: ModelSpec):
        super().__init__(spec)
        self._client = None
        self._types = None

    def check_ready(self) -> None:
        genai = _import("google.genai", "google")
        self._types = _import("google.genai.types", "google")
        key = self._env(self.spec.api_key_env or "GOOGLE_API_KEY")
        self._client = genai.Client(api_key=key)

    def complete(self, request: ChatRequest) -> ChatResponse:
        if self._client is None:
            self.check_ready()
        cfg: dict = {"system_instruction": request.system_text, "temperature": request.temperature,
                     "max_output_tokens": request.max_tokens}
        if request.top_p is not None and self.spec.send_top_p:
            cfg["top_p"] = request.top_p
        if request.seed is not None and self.spec.supports_seed:
            cfg["seed"] = request.seed
        if request.json_mode and self.spec.supports_json_mode:
            cfg["response_mime_type"] = "application/json"
        t0 = time.perf_counter()
        try:
            resp = self._client.models.generate_content(
                model=self.spec.model_id, contents=request.user_text,
                config=self._types.GenerateContentConfig(**cfg))
        except Exception as e:
            raise classify_exception(e) from e
        latency = (time.perf_counter() - t0) * 1000.0
        finish = None
        if getattr(resp, "candidates", None):
            fr = resp.candidates[0].finish_reason
            finish = getattr(fr, "name", None) or (str(fr) if fr is not None else None)
        try:
            text = resp.text
        except Exception as e:  # blocked responses raise on .text in some versions
            raise NonRetryableProviderError(f"no text in response: {e}") from e
        return ChatResponse(
            text=text, finish_reason=finish, usage=_as_dict(getattr(resp, "usage_metadata", None)),
            latency_ms=round(latency, 1), logprobs=None,
            raw_metadata={"served_model": getattr(resp, "model_version", None)}, request_params=cfg,
        )
