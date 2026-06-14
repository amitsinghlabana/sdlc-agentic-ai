"""Helpers mapping pipeline artifacts ↔ GitHub (mirrors ``jira/mapping.py``)."""
from __future__ import annotations

from typing import Iterable, List

from .models import GitHubIssue, RepoFile

# Artifacts we never push to a code repo (machine configs / internal docs).
_SKIP = {"stories.json"}


def artifacts_to_files(artifacts: Iterable, *, skip: set[str] | None = None) -> List[RepoFile]:
    """Turn WorkPackage ``Artifact``/dict items into committable ``RepoFile`` list.

    Accepts either pydantic ``Artifact`` objects or plain dicts ({name, content}).
    """
    skip = _SKIP if skip is None else skip
    files: List[RepoFile] = []
    for a in artifacts:
        name = getattr(a, "name", None) if not isinstance(a, dict) else a.get("name")
        content = getattr(a, "content", None) if not isinstance(a, dict) else a.get("content")
        if not name or name in skip:
            continue
        if not (content or "").strip():
            continue
        files.append(RepoFile(path=name, content=content))
    return files


def issue_to_feature_request(issue: GitHubIssue) -> str:
    """Build a Composer-ready feature-request string from a GitHub issue."""
    lines = [f"Feature request (from GitHub issue #{issue.number}): {issue.title}".strip()]
    if issue.body:
        lines += ["", issue.body.strip()]
    if issue.labels:
        lines += ["", "Labels: " + ", ".join(issue.labels)]
    return "\n".join(lines).strip()

