"""GitHub client factory — picks the provider with a safe fallback to mock.

Mirrors ``jira/factory.py``. ``cloud`` is the real GitHub REST client; until
it's configured (token + repo) it falls back to the free offline mock.
"""
from __future__ import annotations

import logging

from ...config import settings
from .base import GitHubClient
from .mock import MockGitHubClient

logger = logging.getLogger("sdlc.github")

_client: GitHubClient | None = None


def _build() -> GitHubClient:
    if settings.github_provider == "cloud":
        if settings.github_configured:
            try:
                from .cloud import CloudGitHubClient

                logger.info("Using Cloud GitHub client (owner=%s, repo=%s)",
                            settings.github_owner or "-", settings.github_repo or "-")
                return CloudGitHubClient(settings)
            except ImportError:
                logger.warning("GITHUB_PROVIDER=cloud but cloud client unavailable — using mock.")
        else:
            logger.warning("GITHUB_PROVIDER=cloud but GITHUB_TOKEN/owner incomplete — using mock.")

    # Mock: a fully-qualified repo pretends to exist (→ branch+PR demo); an
    # owner-only/empty config simulates a fresh repo (→ create-repo demo).
    logger.info("Using Mock GitHub client (free, offline).")
    has_full_repo = bool(settings.github_repo) and "/" in settings.github_repo
    # Honor empty repo when an owner is set (owner-only mode); else use the demo repo.
    mock_repo = settings.github_repo or ("" if settings.github_owner else "demo/sdlc-app")
    return MockGitHubClient(
        repo=mock_repo,
        owner=settings.github_owner,
        exists=has_full_repo,
    )


def get_github() -> GitHubClient:
    """Return a cached singleton GitHub client."""
    global _client
    if _client is None:
        _client = _build()
    return _client


def reset_github() -> None:
    """Drop the cached client (used by tests)."""
    global _client
    _client = None

