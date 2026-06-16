"""Tests for robust agent output parsing + per-agent token budgets.

These directly target the bug where a Developer response truncated at the token
limit produced ZERO files (the corrupted JSON failed to parse). The parser now
salvages every *complete* artifact from a truncated response.
"""
from __future__ import annotations

import asyncio
import json

from app.agents.base import Agent, parse_json
from app.agents.architect import ArchitectAgent
from app.agents.developer import DeveloperAgent
from app.agents.requirements import RequirementsAgent
from app.agents.tester import TesterAgent
from app.config import settings
from app.llm.base import LLMProvider
from app.models import WorkPackage


# --------------------------------------------------------------------------- #
# parse_json — happy paths
# --------------------------------------------------------------------------- #
def test_parse_plain_json():
    data = parse_json('{"summary": "ok", "artifacts": []}')
    assert data["summary"] == "ok"


def test_parse_fenced_json():
    raw = "```json\n{\"summary\": \"fenced\", \"artifacts\": []}\n```"
    assert parse_json(raw)["summary"] == "fenced"


def test_parse_json_with_prose_around_object():
    raw = 'Sure!\n{"summary": "x", "artifacts": []}\nHope that helps.'
    assert parse_json(raw)["summary"] == "x"


# --------------------------------------------------------------------------- #
# parse_json — truncation recovery (the core fix)
# --------------------------------------------------------------------------- #
def _truncated_developer_json() -> str:
    """A realistic Developer response cut off mid-way through the 2nd file."""
    return (
        '{\n'
        '  "summary": "Implemented a full-stack Todo app.",\n'
        '  "details": "React frontend + Express backend.",\n'
        '  "artifacts": [\n'
        '    {"name": "backend/server.js", "type": "code", "language": "javascript",'
        ' "content": "const express = require(\'express\');\\nconst app = express();"},\n'
        '    {"name": "frontend/src/App.js", "type": "code", "language": "javascript",'
        ' "content": "import React from \'react\';\\nfunction App() {\\n  const errData = awa'
    )


def test_recovers_complete_artifacts_from_truncation():
    data = parse_json(_truncated_developer_json())
    assert data.get("_recovered") is True
    names = [a["name"] for a in data["artifacts"]]
    # The first (complete) file is recovered; the truncated 2nd is dropped.
    assert names == ["backend/server.js"]
    assert "express" in data["artifacts"][0]["content"]
    # Scalar fields survive too.
    assert "Todo app" in data["summary"]


def test_recovers_multiple_complete_artifacts():
    raw = (
        '{"summary": "s", "artifacts": ['
        '{"name": "a.py", "type": "code", "language": "python", "content": "x = 1"},'
        '{"name": "b.py", "type": "code", "language": "python", "content": "y = 2"},'
        '{"name": "c.py", "type": "code", "language": "python", "content": "z = 3'  # truncated
    )
    data = parse_json(raw)
    assert [a["name"] for a in data["artifacts"]] == ["a.py", "b.py"]


def test_braces_in_code_content_do_not_break_recovery():
    raw = (
        '{"summary": "s", "artifacts": ['
        '{"name": "f.js", "type": "code", "language": "javascript",'
        ' "content": "function f() { return {a: 1}; }"},'
        '{"name": "g.js", "type": "code", "language": "javascript", "content": "bad'  # truncated
    )
    data = parse_json(raw)
    assert [a["name"] for a in data["artifacts"]] == ["f.js"]
    assert "{a: 1}" in data["artifacts"][0]["content"]


def test_unparseable_falls_back_without_crashing():
    data = parse_json("totally not json")
    assert data["artifacts"] == []
    assert data["details"] == "totally not json"


# --------------------------------------------------------------------------- #
# Agent.run — per-agent token budget + recovery note
# --------------------------------------------------------------------------- #
class _RecordingLLM(LLMProvider):
    name = "recording"

    def __init__(self, response: str):
        self._response = response
        self.calls: list[dict] = []

    async def complete(self, system, user, *, tag="", json_mode=True, max_tokens=None):
        self.calls.append({"tag": tag, "max_tokens": max_tokens})
        return self._response


def test_code_agents_use_code_token_budget():
    llm = _RecordingLLM('{"summary": "ok", "artifacts": []}')
    wp = WorkPackage("Build a todo app")
    asyncio.run(DeveloperAgent().run(wp, llm))
    asyncio.run(TesterAgent().run(wp, llm))
    assert all(c["max_tokens"] == settings.code_max_tokens for c in llm.calls)


def test_text_agents_use_general_token_budget():
    llm = _RecordingLLM('{"summary": "ok", "artifacts": []}')
    wp = WorkPackage("Build a todo app")
    asyncio.run(ArchitectAgent().run(wp, llm))
    assert llm.calls[0]["max_tokens"] == settings.max_tokens
    assert settings.code_max_tokens > settings.max_tokens


def test_requirements_agent_uses_large_budget():
    """Requirements emits requirements.md + stories.json; it must use the larger
    budget so the second artifact (stories.json) isn't truncated away."""
    llm = _RecordingLLM('{"summary": "ok", "artifacts": []}')
    wp = WorkPackage("Build a todo app")
    asyncio.run(RequirementsAgent().run(wp, llm))
    assert llm.calls[0]["max_tokens"] == settings.code_max_tokens


def test_run_sets_note_on_truncated_recovery():
    llm = _RecordingLLM(_truncated_developer_json())
    wp = WorkPackage("Build a todo app")
    result = asyncio.run(DeveloperAgent().run(wp, llm))
    assert len(result.artifacts) == 1
    assert result.note and "truncated" in result.note.lower()


def test_default_agent_is_not_code():
    assert Agent.emits_code is False
    assert RequirementsAgent.emits_code is False
    assert DeveloperAgent.emits_code is True
    assert TesterAgent.emits_code is True


