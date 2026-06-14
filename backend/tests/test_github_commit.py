"""Tests for the LLM-authored commit/PR metadata generator."""
from __future__ import annotations

import asyncio

from app.integrations.github.commit import CommitInfo, generate_commit
from app.integrations.github.models import RepoFile
from app.llm.base import LLMProvider
from app.llm.mock import MockProvider


def _files():
    return [RepoFile(path="app/auth.py", content="def login(): ..."),
            RepoFile(path="tests/test_auth.py", content="def test(): ...")]


def test_generate_commit_uses_mock_llm():
    info = asyncio.run(generate_commit(MockProvider(), title="Add login", files=_files()))
    assert isinstance(info, CommitInfo)
    assert info.subject.startswith("feat")
    assert "login" in info.subject.lower()
    assert len(info.subject) <= 72
    assert info.pr_title and info.pr_body


def test_generate_commit_lists_changed_files_in_body():
    info = asyncio.run(generate_commit(MockProvider(), title="Add login", files=_files()))
    assert "app/auth.py" in info.pr_body


def test_generate_commit_empty_files_falls_back():
    info = asyncio.run(generate_commit(MockProvider(), title="Nothing", files=[]))
    assert info.subject.startswith("feat")


class _BoomLLM(LLMProvider):
    name = "boom"

    async def complete(self, system, user, *, tag="", json_mode=True, max_tokens=None):
        raise RuntimeError("LLM down")


def test_generate_commit_never_raises_on_llm_error():
    # Publishing must never be blocked by metadata generation.
    info = asyncio.run(generate_commit(_BoomLLM(), title="Resilient", files=_files()))
    assert info.subject.startswith("feat")
    assert "resilient" in info.subject.lower()


class _GarbageLLM(LLMProvider):
    name = "garbage"

    async def complete(self, system, user, *, tag="", json_mode=True, max_tokens=None):
        return "not json at all"


def test_generate_commit_falls_back_on_unparseable():
    info = asyncio.run(generate_commit(_GarbageLLM(), title="Fallback", files=_files()))
    assert info.subject.startswith("feat")

