"""GitHub endpoints: status, inbound import, outbound publish (branch+PR / new repo)."""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..config import settings
from ..integrations.github import get_github
from ..integrations.github.commit import generate_commit
from ..integrations.github.mapping import artifacts_to_files, issue_to_feature_request
from ..llm.factory import get_llm

logger = logging.getLogger("sdlc.github")

router = APIRouter(prefix="/api/github", tags=["github"])


@router.get("/status")
async def status() -> dict:
    """GitHub status for the UI. Never returns the token."""
    client = get_github()
    return {
        "provider": client.name,
        "label": getattr(client, "label", client.name),
        "is_mock": client.name == "mock",
        "configured": settings.github_configured,
        "owner": client.owner,
        "repo": client.repo,
        "repo_url": client.repo_url,
        "has_default_repo": client.has_default_repo,
        "dry_run": settings.github_dry_run,
    }


@router.get("/test")
async def test_github() -> dict:
    """Diagnose the GitHub token: auth, identity, and create-repo capability.

    Mirrors /api/llm/test. Surfaces a readable reason for 403s (wrong owner,
    fine-grained token that can't create repos, missing classic 'repo' scope).
    Never returns the token.
    """
    client = get_github()
    try:
        info = await client.diagnose()
    except Exception as exc:  # noqa: BLE001 — surface a readable reason
        logger.exception("GitHub diagnose failed")
        return {"ok": False, "provider": client.name, "error": f"{type(exc).__name__}: {exc}"[:300]}

    hints: List[str] = []
    if info.get("owner_matches") is False:
        hints.append(
            f"Token authenticates as '{info.get('authenticated_as')}' but GITHUB_OWNER is "
            f"'{info.get('configured_owner')}'. Set GITHUB_OWNER to the token's account, "
            "or use a token owned by that org."
        )
    if info.get("token_type") == "fine-grained":
        hints.append(
            "Fine-grained token: creating repos needs Repository access='All repositories' "
            "AND 'Administration: Read and write'. If create still 403s, use a classic token "
            "with the 'repo' scope (most reliable)."
        )
    elif info.get("token_type") == "classic" and info.get("can_create_repos") is False:
        hints.append("Classic token is missing the 'repo' scope needed to create repositories.")
    return {"ok": True, "is_mock": client.name == "mock", **info, "hints": hints}


@router.get("/import")
async def import_issue(number: int = Query(..., ge=1), repo: Optional[str] = Query(None)) -> dict:
    """Fetch a GitHub issue and build a feature-request string for the Composer."""
    client = get_github()
    try:
        issue = await client.get_issue(number, repo=repo)
    except Exception as exc:  # surface a clean 502 instead of a stack trace
        logger.exception("GitHub import failed for #%s", number)
        raise HTTPException(status_code=502, detail=f"Could not import #{number}: {exc}") from exc
    return {
        "request": issue_to_feature_request(issue),
        "issue": {"number": issue.number, "title": issue.title, "url": issue.url},
    }


@router.get("/repos")
async def repos() -> dict:
    """List repositories the user can target (for the repo picker / toggle)."""
    client = get_github()
    try:
        items = await client.list_repos()
    except Exception as exc:
        logger.exception("GitHub list-repos failed")
        raise HTTPException(status_code=502, detail=f"Could not list repos: {exc}") from exc
    return {"repos": items, "default": client.repo, "provider": client.name}


@router.get("/context")
async def repo_context(repo: str = Query(...), branch: Optional[str] = Query(None)) -> dict:
    """Preview the existing-repo files that would seed the pipeline (edit mode)."""
    client = get_github()
    try:
        files = await client.fetch_repo_context(repo, branch=branch)
    except Exception as exc:
        logger.exception("GitHub context fetch failed for %s", repo)
        raise HTTPException(status_code=502, detail=f"Could not read {repo}: {exc}") from exc
    return {
        "repo": repo,
        "count": len(files),
        "files": [{"path": f.path, "bytes": len((f.content or "").encode("utf-8"))} for f in files],
        "provider": client.name,
    }


class PublishArtifact(BaseModel):
    name: str
    content: str = ""


class PublishRequest(BaseModel):
    title: str
    artifacts: List[PublishArtifact]
    body: str = ""
    branch: Optional[str] = None
    # Target a specific repo (else the configured default). Enables multi-repo.
    # "owner/name" → that repo; just "owner" or empty → create a new repo.
    repo: Optional[str] = None
    # Force creating a brand-new repo even if a name is present.
    create_new: bool = False
    private: Optional[bool] = None
    # Original feature request — improves the AI-authored commit message.
    request: str = ""


@router.post("/publish")
async def publish(body: PublishRequest) -> dict:
    """Publish the SELECTED generated artifacts to GitHub (human-in-the-loop).

    The caller chooses the files (``artifacts``) and the target repo (``repo``).
    With ``owner/name`` it opens a PR against that repo; with just an owner (or
    nothing) it creates a new repo. The commit message + PR text are authored by
    the LLM.
    """
    files = artifacts_to_files(body.artifacts)
    if not files:
        raise HTTPException(status_code=400, detail="No publishable files selected.")

    client = get_github()
    private = settings.github_private if body.private is None else body.private

    # Let the AI author the commit + PR metadata (free/deterministic in mock mode).
    commit = await generate_commit(
        get_llm(), title=body.title or "SDLC feature", files=files, request=body.request
    )

    try:
        result = await client.publish(
            files,
            title=body.title or "SDLC feature",
            repo=body.repo,
            create_new=body.create_new,
            private=private,
            body=body.body or commit.pr_body,
            branch=body.branch,
            commit_message=commit.subject,
        )
    except Exception as exc:
        logger.exception("GitHub publish failed")
        raise HTTPException(status_code=502, detail=f"GitHub publish failed: {exc}") from exc

    return {"provider": client.name, "commit": commit.model_dump(), **result.model_dump()}

