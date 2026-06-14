"""Shared pytest fixtures — keep the whole suite hermetic, offline, and $0.

The developer's ``.env`` may point at **real** Azure OpenAI, Foundry IQ, and
JIRA (that's expected for running the app). Tests must never depend on that:
no network, no token spend, fully deterministic. This autouse fixture pins the
LLM and knowledge providers to their free mock implementations and resets the
cached singletons around every test.

Tests that specifically validate real-provider *selection* (e.g. the factory
tests) simply ``monkeypatch`` the provider themselves afterwards — their setattr
runs after this fixture, so it wins for the duration of that test.
"""
from __future__ import annotations

import pytest

from app import runtime_config as rc
from app.config import settings
from app.integrations.github import reset_github
from app.integrations.knowledge import reset_knowledge
from app.llm.factory import reset_llm


@pytest.fixture(autouse=True)
def _force_mock_providers(monkeypatch, tmp_path):
    # Isolate the runtime overrides file so tests never read/write the real one.
    monkeypatch.setattr(rc, "CONFIG_PATH", tmp_path / "runtime-config.json")
    monkeypatch.setattr(settings, "llm_provider", "mock")
    monkeypatch.setattr(settings, "knowledge_provider", "mock")
    monkeypatch.setattr(settings, "github_provider", "mock")
    # Neutralize GitHub owner/repo so tests don't inherit the developer's .env
    # (tests that need them set their own via monkeypatch).
    monkeypatch.setattr(settings, "github_owner", "")
    monkeypatch.setattr(settings, "github_repo", "")
    reset_llm()
    reset_knowledge()
    reset_github()
    yield
    reset_llm()
    reset_knowledge()
    reset_github()

