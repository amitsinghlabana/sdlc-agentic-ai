"""Tests for runtime provider switching (mock↔live without restart/commit).

Offline/free: the conftest fixture points runtime_config.CONFIG_PATH at a temp
file, so these never touch the real overrides file or hit the network.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app import runtime_config as rc
from app.config import settings
from app.main import app

client = TestClient(app)


# --------------------------------------------------------------------------- #
# runtime_config unit behavior
# --------------------------------------------------------------------------- #
def test_set_and_load_overrides_roundtrip():
    rc.set_overrides(settings, {"github_provider": "cloud"})
    assert rc.load() == {"github_provider": "cloud"}
    assert settings.github_provider == "cloud"


def test_set_overrides_rejects_unknown_key():
    try:
        rc.set_overrides(settings, {"not_a_provider": "x"})
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_set_overrides_rejects_invalid_value():
    try:
        rc.set_overrides(settings, {"llm_provider": "gemini"})
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_clear_overrides_reverts_to_env_snapshot():
    settings._env_providers = {
        "llm_provider": "mock", "jira_provider": "mock",
        "knowledge_provider": "mock", "github_provider": "mock",
    }
    rc.set_overrides(settings, {"github_provider": "cloud"})
    assert settings.github_provider == "cloud"
    rc.clear_overrides(settings)
    assert settings.github_provider == "mock"
    assert rc.load() == {}


# --------------------------------------------------------------------------- #
# /api/admin/providers endpoints
# --------------------------------------------------------------------------- #
def test_get_providers_lists_all_four():
    data = client.get("/api/admin/providers").json()
    assert set(data["providers"]) == {"llm", "knowledge", "jira", "github"}
    assert data["providers"]["llm"]["effective"] == "mock"


def test_post_switches_selected_and_persists():
    data = client.post("/api/admin/providers", json={"github_provider": "cloud"}).json()
    assert data["providers"]["github"]["selected"] == "cloud"
    assert data["overrides"]["github_provider"] == "cloud"


def test_post_unconfigured_live_falls_back_effective_mock(monkeypatch):
    # github not configured (no token/repo) → selected cloud, effective mock.
    monkeypatch.setattr(settings, "github_token", "")
    monkeypatch.setattr(settings, "github_repo", "")
    data = client.post("/api/admin/providers", json={"github_provider": "cloud"}).json()
    assert data["providers"]["github"]["selected"] == "cloud"
    assert data["providers"]["github"]["effective"] == "mock"
    assert data["providers"]["github"]["configured"] is False


def test_post_empty_body_is_400():
    resp = client.post("/api/admin/providers", json={})
    assert resp.status_code == 400


def test_post_invalid_value_is_400():
    resp = client.post("/api/admin/providers", json={"knowledge_provider": "bogus"})
    assert resp.status_code == 400


def test_reset_endpoint_clears_overrides():
    settings._env_providers = {
        "llm_provider": "mock", "jira_provider": "mock",
        "knowledge_provider": "mock", "github_provider": "mock",
    }
    client.post("/api/admin/providers", json={"jira_provider": "cloud"})
    data = client.post("/api/admin/providers/reset").json()
    assert data["overrides"] == {}
    assert data["providers"]["jira"]["selected"] == "mock"

