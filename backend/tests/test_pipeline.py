"""End-to-end pipeline tests (mock provider — free, deterministic)."""
from __future__ import annotations

import asyncio

from app.llm.mock import MockProvider
from app.orchestrator import run_pipeline


def _collect(request: str) -> list[dict]:
    async def go() -> list[dict]:
        return [ev async for ev in run_pipeline(request, MockProvider())]

    return asyncio.run(go())


def test_pipeline_produces_core_artifacts():
    events = _collect("Add a login page with email/password")
    types = [e["type"] for e in events]

    assert types[0] == "run_start"
    assert "plan" in types
    assert types[-1] == "run_complete"

    names = {e["artifact"]["name"] for e in events if e["type"] == "artifact"}
    assert "requirements.md" in names
    assert "design.md" in names
    assert "app/auth.py" in names
    assert "tests/test_auth.py" in names
    assert "README_feature.md" in names


def test_reviewer_feedback_loop_runs_and_resolves():
    events = _collect("Add a login page with email/password")

    # The reviewer should request changes at least once (plaintext password bug)...
    loop_events = [e for e in events if e["type"] == "loop"]
    assert len(loop_events) >= 1

    # ...and the final reviewer verdict should be approve.
    reviewer_verdicts = [
        e.get("verdict") for e in events if e["type"] == "agent_done" and e["agent"] == "reviewer"
    ]
    assert reviewer_verdicts[-1] == "approve"

    # Final code should contain the bcrypt fix.
    auth_versions = [
        e["artifact"]["content"]
        for e in events
        if e["type"] == "artifact" and e["artifact"]["name"] == "app/auth.py"
    ]
    assert "bcrypt" in auth_versions[-1]


def test_run_complete_lists_artifacts():
    events = _collect("Build a contact form")
    run_complete = next(e for e in events if e["type"] == "run_complete")
    assert run_complete["artifacts"], "expected a non-empty artifact summary"
    assert "duration_ms" in run_complete

