"""Provider interface shared by the mock and the real model back-ends."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..config import ModelSpec


@dataclass
class ChatRequest:
    messages: list[dict]              # [{"role": "system"|"user", "content": str}, ...]
    temperature: float
    top_p: float | None
    max_tokens: int
    seed: int | None = None
    json_mode: bool = False
    want_logprobs: bool = False
    top_logprobs: int = 5
    logprobs_max_tokens: int = 40
    extra_params: dict = field(default_factory=dict)   # provider-specific sampling params (e.g. vLLM top_k)

    @property
    def system_text(self) -> str:
        return "\n\n".join(m["content"] for m in self.messages if m["role"] == "system")

    @property
    def user_text(self) -> str:
        return "\n\n".join(m["content"] for m in self.messages if m["role"] == "user")


@dataclass
class ChatResponse:
    text: str | None
    finish_reason: str | None
    usage: dict | None
    latency_ms: float
    logprobs: Any | None = None
    raw_metadata: dict = field(default_factory=dict)
    request_params: dict = field(default_factory=dict)   # what was actually sent (minus messages)


class ProviderError(Exception):
    """Base class for provider failures. ``retryable`` decides the retry policy."""

    retryable = False

    def __init__(self, message: str, *, status_code: int | None = None, detail: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail

    def to_record(self) -> dict:
        return {"type": type(self).__name__, "message": str(self)[:2000],
                "status_code": self.status_code, "retryable": self.retryable}


class RetryableProviderError(ProviderError):
    """Transient failure (rate limit, timeout, 5xx, connection): retry with backoff."""

    retryable = True


class NonRetryableProviderError(ProviderError):
    """Permanent failure (bad request, auth, unknown model): record and move on."""

    retryable = False


class ProviderConfigError(RuntimeError):
    """Misconfiguration detected before any call (missing env var, missing SDK)."""


RETRYABLE_STATUS = {408, 409, 425, 429}
RETRYABLE_NAME_HINTS = ("Timeout", "Connection", "RateLimit", "Overloaded", "ServiceUnavailable",
                        "InternalServer", "Unavailable", "TooManyRequests")


def classify_exception(exc: BaseException) -> ProviderError:
    """Map an SDK / network exception to a retryable or non-retryable ProviderError."""
    if isinstance(exc, ProviderError):
        return exc
    status = getattr(exc, "status_code", None)
    if status is None:
        status = getattr(exc, "code", None)
    if status is None:
        status = getattr(getattr(exc, "response", None), "status_code", None)
    name = type(exc).__name__
    msg = f"{name}: {exc}"
    if isinstance(status, int):
        if status in RETRYABLE_STATUS or status >= 500:
            return RetryableProviderError(msg, status_code=status)
        return NonRetryableProviderError(msg, status_code=status)
    if isinstance(exc, (TimeoutError, ConnectionError)) or any(h in name for h in RETRYABLE_NAME_HINTS):
        return RetryableProviderError(msg)
    return NonRetryableProviderError(msg)


def trim_logprobs(content: list | None, max_tokens: int) -> list | None:
    """Keep ``[{token, logprob, top: [{token, logprob}]}]`` for the first N tokens."""
    if not content:
        return None
    out = []
    for item in content[:max_tokens]:
        get = item.get if isinstance(item, dict) else (lambda k, d=None, _i=item: getattr(_i, k, d))
        tops = get("top_logprobs") or []
        out.append({
            "token": get("token"),
            "logprob": get("logprob"),
            "top": [
                {"token": (t.get("token") if isinstance(t, dict) else getattr(t, "token", None)),
                 "logprob": (t.get("logprob") if isinstance(t, dict) else getattr(t, "logprob", None))}
                for t in tops
            ],
        })
    return out


class Provider(ABC):
    """A chat-completion back-end bound to one model."""

    name: str = "base"
    is_mock: bool = False

    def __init__(self, spec: ModelSpec):
        self.spec = spec

    @abstractmethod
    def complete(self, request: ChatRequest) -> ChatResponse:
        """Make one call. Raise RetryableProviderError / NonRetryableProviderError on failure."""

    def check_ready(self) -> None:
        """Raise ProviderConfigError if the provider cannot be used (called once before a run)."""

    def introspect(self) -> dict:
        """Best-effort provenance from the serving side (A6). Unknown -> empty dict, never guessed."""
        return {}

    # helpers for subclasses
    def _env(self, var: str | None, required: bool = True) -> str | None:
        if not var:
            return None
        val = os.environ.get(var)
        if required and not val:
            raise ProviderConfigError(f"environment variable {var} is not set (model {self.spec.alias})")
        return val
