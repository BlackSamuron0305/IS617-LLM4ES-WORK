"""Model back-ends. Real providers are imported lazily and never used in tests."""

from __future__ import annotations

from ..config import MockCfg, ModelSpec, NationalitySet, PrincipleSpec
from .base import (ChatRequest, ChatResponse, NonRetryableProviderError, Provider, ProviderConfigError,
                   ProviderError, RetryableProviderError, classify_exception)

__all__ = [
    "ChatRequest", "ChatResponse", "Provider", "ProviderError", "RetryableProviderError",
    "NonRetryableProviderError", "ProviderConfigError", "classify_exception", "make_provider",
]


def make_provider(spec: ModelSpec, mock_cfg: MockCfg | None = None,
                  nationalities: NationalitySet | None = None, principle: PrincipleSpec | None = None) -> Provider:
    """Instantiate the provider for ``spec`` (no network activity happens here)."""
    if spec.provider == "mock":
        from .mock import MockProvider

        if nationalities is None:
            raise ValueError("the mock provider needs the nationality set")
        return MockProvider(spec, mock_cfg or MockCfg(), nationalities.demonym_to_code(), nationalities.codes,
                            principle)
    if spec.provider == "openai_compatible":
        from .openai_compatible import OpenAICompatibleProvider

        return OpenAICompatibleProvider(spec)
    if spec.provider == "openai":
        from .api_providers import OpenAIProvider

        return OpenAIProvider(spec)
    if spec.provider == "anthropic":
        from .api_providers import AnthropicProvider

        return AnthropicProvider(spec)
    if spec.provider == "google":
        from .api_providers import GoogleProvider

        return GoogleProvider(spec)
    if spec.provider == "hf_local":
        from .hf_local import HFLocalProvider

        return HFLocalProvider(spec)
    raise ValueError(f"unknown provider {spec.provider}")
