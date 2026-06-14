"""JIRA client factory — picks the provider with a safe fallback to mock.

Mirrors ``llm/factory.py``. ``cloud`` is wired in P2; until then (or if the
instance isn't configured) it falls back to the free mock client.
"""
from __future__ import annotations

import logging

from ...config import settings
from .base import JiraClient
from .mock import MockJiraClient

logger = logging.getLogger("sdlc.jira")

_client: JiraClient | None = None


def _build() -> JiraClient:
    choice = settings.jira_provider

    if choice == "cloud":
        if settings.jira_configured:
            try:
                from .cloud import CloudJiraClient  # P2

                logger.info("Using Cloud JIRA client (%s)", settings.jira_base_url)
                return CloudJiraClient(settings)
            except ImportError:
                logger.warning("JIRA_PROVIDER=cloud but cloud client not available yet — using mock.")
        else:
            logger.warning("JIRA_PROVIDER=cloud but JIRA_* env vars incomplete — using mock.")

    logger.info("Using Mock JIRA client (free, no account needed).")
    return MockJiraClient(
        base_url=settings.jira_base_url,
        project_key=settings.jira_project_key or "DEMO",
        default_assignee=settings.jira_default_assignee,
    )


def get_jira() -> JiraClient:
    """Return a cached singleton JIRA client."""
    global _client
    if _client is None:
        _client = _build()
    return _client


def reset_jira() -> None:
    """Drop the cached client (used by tests)."""
    global _client
    _client = None

