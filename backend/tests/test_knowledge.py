"""Tests for the Foundry IQ knowledge/grounding layer.

All offline/free: the mock client grounds against in-repo docs; the real
``FoundryKnowledgeClient`` is exercised with an ``httpx.MockTransport`` (no
network, no Azure account). A pipeline test asserts grounding events + a
``grounding.md`` artifact appear and that requirements cite sources.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.integrations.knowledge import get_knowledge, reset_knowledge
from app.integrations.knowledge.foundry import FoundryKnowledgeClient
from app.integrations.knowledge.mock import MockKnowledgeClient
from app.integrations.knowledge.models import Citation, RetrievalResult
from app.main import app

client = TestClient(app)


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
def test_retrieval_result_prompt_and_markdown():
    result = RetrievalResult(
        query="login",
        citations=[Citation(id="S1", title="Password storage", source="security-checklist.md",
                            snippet="hash with bcrypt")],
        subqueries=["standards relevant to 'login'"],
        provider="mock",
    )
    block = result.as_prompt_block()
    assert "[S1] Password storage" in block and "bcrypt" in block
    md = result.to_markdown()
    assert "Grounding (Foundry IQ)" in md and "S1" in md


def test_empty_result_prompt_block_is_blank():
    assert RetrievalResult(query="x").as_prompt_block() == ""


# --------------------------------------------------------------------------- #
# Mock client (grounds against docs/standards via config default)
# --------------------------------------------------------------------------- #
def test_mock_retrieve_returns_relevant_citations():
    kb = MockKnowledgeClient(knowledge_dir=settings.knowledge_dir)
    result = asyncio.run(kb.retrieve("secure login with password", top=3))
    assert 1 <= len(result.citations) <= 3
    assert all(c.id.startswith("S") for c in result.citations)
    # A password query should surface the security section.
    joined = " ".join(c.title + c.snippet for c in result.citations).lower()
    assert "password" in joined or "plaintext" in joined


def test_mock_retrieve_is_deterministic():
    kb = MockKnowledgeClient(knowledge_dir=settings.knowledge_dir)
    a = asyncio.run(kb.retrieve("validation errors", top=3))
    b = asyncio.run(kb.retrieve("validation errors", top=3))
    assert [c.title for c in a.citations] == [c.title for c in b.citations]


def test_mock_retrieve_fallback_when_no_dir(tmp_path):
    kb = MockKnowledgeClient(knowledge_dir=str(tmp_path))  # empty dir → built-in fallback
    result = asyncio.run(kb.retrieve("anything", top=2))
    assert len(result.citations) >= 1


# --------------------------------------------------------------------------- #
# Real Foundry IQ client via httpx MockTransport
# --------------------------------------------------------------------------- #
def _foundry_settings(**overrides):
    base = dict(
        foundry_search_endpoint="https://example.search.windows.net",
        foundry_knowledge_agent="sdlc-knowledge-agent",
        foundry_index="sdlc-standards",
        foundry_api_version="2025-08-01-preview",
        foundry_api_key="secret-key",
        knowledge_ca_bundle="",
        knowledge_verify_ssl=True,
        request_timeout=30.0,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_foundry_retrieve_parses_references_and_sends_key():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["api_key"] = request.headers.get("api-key")
        captured["query"] = request.url.params.get("api-version")
        return httpx.Response(200, json={
            "references": [
                {"rerankerScore": 2.5, "sourceData": {
                    "title": "Password storage", "content": "hash with bcrypt", "source": "security-checklist.md"}},
                {"rerankerScore": 1.1, "sourceData": {
                    "title": "Input validation", "content": "validate server-side"}},
            ],
            "activity": [{"query": {"search": "password hashing standards"}}],
        })

    kb = FoundryKnowledgeClient(_foundry_settings(), transport=httpx.MockTransport(handler))
    result = asyncio.run(kb.retrieve("secure login", top=5))

    assert captured["api_key"] == "secret-key"
    assert "/agents/sdlc-knowledge-agent/retrieve" in captured["path"]
    assert captured["query"] == "2025-08-01-preview"
    assert [c.id for c in result.citations] == ["S1", "S2"]
    assert result.citations[0].title == "Password storage"
    assert result.citations[0].score == 2.5
    assert result.subqueries == ["password hashing standards"]


def test_foundry_retrieve_falls_back_to_response_text():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "response": [{"content": [{"type": "text", "text": "Grounded summary text"}]}],
        })

    kb = FoundryKnowledgeClient(_foundry_settings(), transport=httpx.MockTransport(handler))
    result = asyncio.run(kb.retrieve("q", top=3))
    assert len(result.citations) == 1
    assert "Grounded summary" in result.citations[0].snippet


def test_foundry_parses_real_response_json_array():
    """Real agentic-retrieval shape: citations are a JSON array embedded in the
    response text, while references[].sourceData is null."""
    import json as _json

    embedded = _json.dumps([
        {"ref_id": 0, "title": "S-1 Password storage", "terms": "security-checklist.md",
         "content": "Passwords must NEVER be stored in plaintext."},
        {"ref_id": 1, "title": "S-2 Authentication errors", "terms": "security-checklist.md",
         "content": "Failed logins return a generic 401."},
    ])

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "response": [{"role": "assistant", "content": [{"type": "text", "text": embedded}]}],
            "references": [
                {"type": "AzureSearchDoc", "id": "0", "sourceData": None, "docKey": "security-checklist-md--s-1"},
                {"type": "AzureSearchDoc", "id": "1", "sourceData": None, "docKey": "security-checklist-md--s-2"},
            ],
        })

    kb = FoundryKnowledgeClient(_foundry_settings(), transport=httpx.MockTransport(handler))
    result = asyncio.run(kb.retrieve("secure login", top=4))
    assert [c.id for c in result.citations] == ["S1", "S2"]
    assert result.citations[0].title == "S-1 Password storage"
    assert result.citations[0].source == "security-checklist.md"
    assert "plaintext" in result.citations[0].snippet


def test_foundry_error_returns_empty_not_raise():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": "forbidden"})

    kb = FoundryKnowledgeClient(_foundry_settings(), transport=httpx.MockTransport(handler))
    result = asyncio.run(kb.retrieve("q"))
    assert result.citations == [] and result.provider == "foundry"


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #
def test_factory_defaults_to_mock():
    reset_knowledge()
    try:
        assert get_knowledge().name == "mock"
    finally:
        reset_knowledge()


def test_factory_selects_foundry_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "knowledge_provider", "foundry")
    monkeypatch.setattr(settings, "foundry_search_endpoint", "https://example.search.windows.net")
    monkeypatch.setattr(settings, "foundry_knowledge_agent", "sdlc-knowledge-agent")
    monkeypatch.setattr(settings, "foundry_api_key", "secret")
    reset_knowledge()
    try:
        client_obj = get_knowledge()
        assert client_obj.name == "foundry"
        assert "Foundry IQ" in client_obj.label
    finally:
        reset_knowledge()


# --------------------------------------------------------------------------- #
# Endpoints + pipeline grounding (mock provider)
# --------------------------------------------------------------------------- #
def test_knowledge_status_endpoint():
    reset_knowledge()
    data = client.get("/api/knowledge/status").json()
    assert data["provider"] == "mock" and data["is_mock"] is True
    assert "api_key" not in data and "key" not in data


def test_knowledge_test_endpoint_returns_citations():
    reset_knowledge()
    data = client.get("/api/knowledge/test").json()
    assert data["ok"] is True
    assert data["count"] >= 1


def test_pipeline_emits_grounding_and_cites_sources():
    reset_knowledge()
    resp = client.post("/api/run", json={"request": "Add secure email/password login"}).json()
    names = {a["name"] for a in resp["artifacts"]}
    assert "grounding.md" in names
    # A grounding event carries citations.
    grounding_events = [e for e in resp["events"] if e["type"] == "grounding"]
    assert grounding_events and grounding_events[0]["count"] >= 1
    # Requirements cite a source inline.
    reqs = next(a for a in resp["artifacts"] if a["name"] == "requirements.md")
    assert "[S1]" in reqs["content"]

