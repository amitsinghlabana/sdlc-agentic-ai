"""Provider factory — picks the configured backend with a safe fallback to mock."""
from __future__ import annotations

import logging

from ..config import settings
from .base import LLMProvider
from .mock import MockProvider

logger = logging.getLogger("sdlc.llm")

_provider: LLMProvider | None = None


def _build() -> LLMProvider:
    choice = settings.llm_provider

    if choice == "azure":
        if settings.azure_configured:
            from .azure_openai import AzureOpenAIProvider

            logger.info("Using Azure OpenAI provider (deployment=%s)", settings.azure_openai_deployment)
            return AzureOpenAIProvider(settings)
        logger.warning("LLM_PROVIDER=azure but AZURE_OPENAI_ENDPOINT/KEY missing — falling back to mock.")

    elif choice == "openai":
        if settings.openai_configured:
            from .openai_provider import OpenAIProvider

            logger.info("Using OpenAI provider (model=%s)", settings.openai_model)
            return OpenAIProvider(settings)
        logger.warning("LLM_PROVIDER=openai but OPENAI_API_KEY missing — falling back to mock.")

    logger.info("Using Mock provider (free, no tokens spent).")
    return MockProvider()


def get_llm() -> LLMProvider:
    """Return a cached singleton provider instance."""
    global _provider
    if _provider is None:
        _provider = _build()
    return _provider


def reset_llm() -> None:
    """Drop the cached provider (used by tests)."""
    global _provider
    _provider = None

