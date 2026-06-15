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


def test_review_loop_caps_and_addresses_final_feedback(monkeypatch):
    """A reviewer that never approves must not strand the pipeline.

    When the iteration cap is hit while changes are still requested, the
    Developer applies one FINAL revision (feedback is never dropped), the loop
    is flagged ``final``, and the run still completes through documentation —
    rather than abruptly jumping to docs on an unresolved "request_changes".
    """
    from app.config import settings
    from app.llm.mock import MockProvider

    monkeypatch.setattr(settings, "max_review_loops", 1)

    class StubbornReviewerMock(MockProvider):
        """Reviewer that always requests changes — exercises the cap path."""

        def _reviewer(self, title: str, user: str) -> dict:
            return {
                "summary": "Requested changes.",
                "details": "## Review — 🔁 Changes requested\n\n- Still needs work.\n",
                "verdict": "request_changes",
                "comments": ["Improve error handling."],
                "artifacts": [],
            }

    async def go() -> list[dict]:
        return [ev async for ev in run_pipeline("Add a login page", StubbornReviewerMock())]

    events = asyncio.run(go())

    # The run still completes through documentation.
    assert events[-1]["type"] == "run_complete"
    names = {e["artifact"]["name"] for e in events if e["type"] == "artifact"}
    assert "README_feature.md" in names

    # Reviewer is bounded to max_review_loops + 1 runs (here: 2).
    reviewer_runs = [e for e in events if e["type"] == "agent_start" and e["agent"] == "reviewer"]
    assert len(reviewer_runs) == 2

    # Exactly one loop is flagged ``final`` (the capped iteration).
    final_loops = [e for e in events if e["type"] == "loop" and e.get("final")]
    assert len(final_loops) == 1

    # The Developer addressed the FINAL feedback: it ran the initial pass plus a
    # revision per loop (2) = 3 times, so the review phase ends on a Developer
    # revision — not on an unaddressed reviewer "request_changes".
    dev_runs = [e for e in events if e["type"] == "agent_start" and e["agent"] == "developer"]
    assert len(dev_runs) == 3


