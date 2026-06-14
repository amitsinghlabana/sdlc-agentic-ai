"""Knowledge client factory — picks the provider with a safe fallback to mock.

Mirrors ``llm/factory.py`` and ``jira/factory.py``. ``foundry`` is the real
**Foundry IQ** agentic-retrieval client; until it's configured (or if its deps
aren't available) it falls back to the free, offline mock client.
"""
from __future__ import annotations

import logging

from ...config import settings
from .base import KnowledgeClient
from .mock import MockKnowledgeClient

logger = logging.getLogger("sdlc.knowledge")

_client: KnowledgeClient | None = None


def _build() -> KnowledgeClient:
    choice = settings.knowledge_provider

    if choice == "foundry":
        if settings.knowledge_configured:
            try:
                from .foundry import FoundryKnowledgeClient

                logger.info("Using Foundry IQ knowledge client (%s)", settings.foundry_search_endpoint)
                return FoundryKnowledgeClient(settings)
            except ImportError:
                logger.warning("KNOWLEDGE_PROVIDER=foundry but client unavailable — using mock.")
        else:
            logger.warning("KNOWLEDGE_PROVIDER=foundry but FOUNDRY_* env vars incomplete — using mock.")

    logger.info("Using Mock knowledge client (free, offline grounding).")
    return MockKnowledgeClient(knowledge_dir=settings.knowledge_dir)


def get_knowledge() -> KnowledgeClient:
    """Return a cached singleton knowledge client."""
    global _client
    if _client is None:
        _client = _build()
    return _client


def reset_knowledge() -> None:
    """Drop the cached client (used by tests)."""
    global _client
    _client = None

