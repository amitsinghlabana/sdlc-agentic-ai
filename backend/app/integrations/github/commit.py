"""LLM-authored commit + PR messages for the publish step.

Keeps the AI in the loop for Git metadata: given the feature and the changed
files, the model writes a Conventional Commits subject/body and a PR title/body.
Works offline too — the mock LLM returns deterministic text via its ``committer``
template, so the whole flow is demoable and unit-testable for $0.
"""
from __future__ import annotations

import logging
from typing import List

from pydantic import BaseModel

from ...agents.base import parse_json
from ...llm.base import LLMProvider
from ...prompts import personas
from .models import RepoFile

logger = logging.getLogger("sdlc.github")


class CommitInfo(BaseModel):
    """AI-authored Git metadata for a publish."""

    subject: str
    body: str = ""
    pr_title: str = ""
    pr_body: str = ""


def _fallback(title: str, files: List[RepoFile]) -> CommitInfo:
    subject = (f"feat: {title}".strip() or "feat: update")[:72]
    listing = "\n".join(f"- `{f.path}`" for f in files)
    body = f"Automated change from the SDLC Agentic AI pipeline.\n\nFiles:\n{listing}"
    return CommitInfo(subject=subject, body=body, pr_title=subject[:120], pr_body=body)


async def generate_commit(
    llm: LLMProvider, *, title: str, files: List[RepoFile], request: str = ""
) -> CommitInfo:
    """Ask the LLM for a commit message + PR title/body. Never raises.

    Falls back to a sensible ``feat:`` line if the model is unavailable or the
    response can't be parsed, so publishing is never blocked on this step.
    """
    if not files:
        return _fallback(title, files)

    listing = "\n".join(f"- {f.path}" for f in files)
    user = (
        f"Feature: {title}\n"
        + (f"Original request: {request}\n" if request else "")
        + f"\nChanged files:\n{listing}\n\n"
        "Write the Git metadata for this change."
    )
    try:
        raw = await llm.complete(
            personas.COMMITTER, user, tag="committer", json_mode=True, max_tokens=400
        )
        data = parse_json(raw)
    except Exception:  # noqa: BLE001 — never block publishing on metadata
        logger.warning("commit-message generation failed; using fallback", exc_info=True)
        return _fallback(title, files)

    subject = (data.get("subject") or "").strip()
    if not subject:
        return _fallback(title, files)
    body = (data.get("body") or "").strip()
    return CommitInfo(
        subject=subject[:72],
        body=body,
        pr_title=(data.get("pr_title") or subject).strip()[:120],
        pr_body=(data.get("pr_body") or body).strip(),
    )

