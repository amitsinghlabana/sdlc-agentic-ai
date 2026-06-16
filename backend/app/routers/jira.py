"""JIRA endpoints: status, inbound import, outbound create-stories."""
from __future__ import annotations

import logging
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..config import settings
from ..integrations.jira import get_jira
from ..integrations.jira.mapping import issue_to_feature_request, normalize_issue_key
from ..integrations.jira.models import CreatedIssue, Epic, Story, Subtask

logger = logging.getLogger("sdlc.jira")

router = APIRouter(prefix="/api/jira", tags=["jira"])


def _host() -> str:
    if settings.jira_base_url:
        return urlparse(settings.jira_base_url).netloc or settings.jira_base_url
    return "demo.atlassian.net"


@router.get("/status")
async def status() -> dict:
    """JIRA equivalent of /api/config. Never returns the token."""
    client = get_jira()
    return {
        "provider": client.name,
        "label": getattr(client, "label", client.name),
        "is_mock": client.name == "mock",
        "configured": settings.jira_configured,
        "host": _host(),
        "project_key": settings.jira_project_key or "DEMO",
        "dry_run": settings.jira_dry_run,
        "default_assignee": settings.jira_default_assignee or None,
    }


@router.get("/projects")
async def projects() -> dict:
    """List visible projects — a handy 'is my connection working?' check."""
    client = get_jira()
    try:
        items = await client.list_projects()
    except Exception as exc:  # surface a clean 502 instead of a stack trace
        logger.exception("JIRA list-projects failed")
        raise HTTPException(status_code=502, detail=f"Could not list projects: {exc}") from exc
    return {"projects": items, "provider": client.name}


@router.get("/import")
async def import_issue(key: str = Query(..., min_length=1)) -> dict:
    """Fetch a JIRA issue and build a feature-request string for the Composer.

    ``key`` may be a bare issue key (``MAV-26``) or a pasted JIRA URL such as
    ``.../browse/MAV-26`` or ``...?selectedIssue=MAV-26`` — the key is extracted.
    """
    try:
        issue_key = normalize_issue_key(key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    client = get_jira()
    try:
        issue = await client.get_issue(issue_key)
    except Exception as exc:  # surface a clean 502 instead of a stack trace
        logger.exception("JIRA import failed for %s", issue_key)
        raise HTTPException(status_code=502, detail=f"Could not import {issue_key}: {exc}") from exc
    return {
        "request": issue_to_feature_request(issue),
        "issue": {"key": issue.key, "summary": issue.summary, "type": issue.issue_type},
    }


class CreateStoriesRequest(BaseModel):
    stories: List[Story]
    epic: Optional[Epic] = None
    create_epic: bool = False
    # Context from an inbound import (so we attach to the existing issue instead
    # of always creating a brand-new epic + stories):
    #   - import_type == "Epic"  → link stories UNDER import_key + update its details
    #   - import_type == "Story" → create sub-tasks UNDER import_key (no new stories)
    import_key: Optional[str] = None
    import_type: Optional[str] = None


def _gather_subtasks(stories: List[Story]) -> List[Subtask]:
    """Flatten generated stories into a list of sub-tasks.

    Uses each story's explicit sub-tasks when present; otherwise falls back to
    the story itself as a single sub-task. Lets an imported Story be broken down
    into actionable sub-tasks.
    """
    subs: List[Subtask] = []
    for s in stories:
        if s.subtasks:
            subs.extend(s.subtasks)
        else:
            subs.append(Subtask(summary=s.summary[:255], description=s.description))
    return subs


async def _create_for_import(
    client, body: "CreateStoriesRequest", import_key: str, import_type: str
) -> Optional[dict]:
    """Handle create when an issue was imported. Returns None for a fresh run."""
    # Imported a Story → add sub-tasks under it.
    if import_type in {"story", "task", "bug", "sub-task", "subtask"}:
        subtasks = _gather_subtasks(body.stories)
        created = await client.bulk_create_subtasks(subtasks, parent_key=import_key)
        return {
            "epic": None,
            "created": [c.model_dump() for c in created],
            "count": len(created),
            "provider": client.name,
            "mode": "subtasks",
            "parent": import_key,
        }

    # Imported an Epic → link stories under it + refresh its details.
    if import_type == "epic":
        epic_updated: Optional[CreatedIssue] = None
        if body.epic is not None:
            epic_updated = await client.update_issue(import_key, description=body.epic.description)
        created = await client.bulk_create(body.stories, parent_key=import_key)
        return {
            "epic": (epic_updated.model_dump() if epic_updated else None),
            "created": [c.model_dump() for c in created],
            "count": len(created),
            "provider": client.name,
            "mode": "epic_children",
            "parent": import_key,
        }

    return None


@router.post("/create-stories")
async def create_stories(body: CreateStoriesRequest) -> dict:
    """Create the generated work in JIRA (human-in-the-loop action).

    Behavior depends on what (if anything) was imported:
    - Imported an **Epic** → create the stories *under that epic* and refresh its
      description (does NOT create a second epic).
    - Imported a **Story** → create sub-tasks *under that story* (no new stories).
    - Nothing imported → create a new epic (optional) + the stories.
    """
    if not body.stories:
        raise HTTPException(status_code=400, detail="No stories provided.")

    client = get_jira()
    import_type = (body.import_type or "").strip().lower()
    import_key = (body.import_key or "").strip().upper() or None

    try:
        if import_key and import_type:
            result = await _create_for_import(client, body, import_key, import_type)
            if result is not None:
                return result

        # Fresh run (nothing imported) → new epic (optional) + stories.
        epic_created: Optional[CreatedIssue] = None
        parent_key: Optional[str] = None
        if body.create_epic and body.epic is not None:
            epic_created = await client.create_epic(body.epic)
            parent_key = epic_created.key
        created = await client.bulk_create(body.stories, parent_key=parent_key)
    except Exception as exc:
        logger.exception("JIRA create-stories failed")
        raise HTTPException(status_code=502, detail=f"JIRA create failed: {exc}") from exc

    return {
        "epic": epic_created.model_dump() if epic_created else None,
        "created": [c.model_dump() for c in created],
        "count": len(created),
        "provider": client.name,
        "mode": "new",
        "parent": parent_key,
    }

