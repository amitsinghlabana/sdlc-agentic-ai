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
from ..integrations.jira.models import CreatedIssue, Epic, Story

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


@router.post("/create-stories")
async def create_stories(body: CreateStoriesRequest) -> dict:
    """Create the generated stories in JIRA (human-in-the-loop action)."""
    if not body.stories:
        raise HTTPException(status_code=400, detail="No stories provided.")

    client = get_jira()
    epic_created: Optional[CreatedIssue] = None
    parent_key: Optional[str] = None

    try:
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
    }

