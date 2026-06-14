"""Pydantic models for the GitHub integration (provider-agnostic).

Kept dependency-free so the mock client + unit tests need no network. Mirrors
the shape of ``jira/models.py``.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class RepoRef(BaseModel):
    """A reference to a repository."""

    owner: str
    name: str
    default_branch: str = "main"
    url: str = ""


class RepoFile(BaseModel):
    """A single file to commit (path + full content)."""

    path: str
    content: str = ""
    sha: str = ""  # blob sha when updating an existing file (filled by the client)


class PullRequest(BaseModel):
    """A created pull request."""

    number: int
    url: str
    branch: str
    base: str = "main"
    title: str = ""


class GitHubIssue(BaseModel):
    """An issue imported as a feature request (inbound)."""

    number: int
    title: str = ""
    body: str = ""
    labels: List[str] = Field(default_factory=list)
    url: str = ""


class PublishResult(BaseModel):
    """Outcome of publishing the pipeline's artifacts to GitHub.

    ``mode`` is auto-selected by whether the target repo already exists:
      * ``new_repo``     — a new repo was created and files pushed to its default branch.
      * ``pull_request`` — a branch was created, files committed, and a PR opened.
    """

    mode: str  # "new_repo" | "pull_request"
    repo: str  # "owner/name"
    repo_url: str
    branch: str
    files: int
    html_url: str  # the primary link to show (repo for new, PR for existing)
    pull_request: Optional[PullRequest] = None
    dry_run: bool = False

