"""Mapping helpers: stories.json parsing, ADF build/flatten, request builder.

Kept provider-agnostic and dependency-free so it is trivially unit-testable.
"""
from __future__ import annotations

import json
import re
from typing import List
from urllib.parse import parse_qs, urlparse

from .models import JiraIssue, Story, StoryBundle, Subtask


# --------------------------------------------------------------------------- #
# Issue-key normalization (inbound import is tolerant of pasted URLs)
# --------------------------------------------------------------------------- #
# A JIRA issue key: project key (letter, then word chars) + '-' + number.
_KEY = r"[A-Za-z]\w*-\d+"
_ISSUE_KEY_RE = re.compile(_KEY)
_FULL_KEY_RE = re.compile(rf"^{_KEY}$")
_BROWSE_RE = re.compile(rf"/browse/({_KEY})", re.IGNORECASE)
# Query params that commonly carry the key in Atlassian URLs (checked lower-cased).
_KEY_PARAMS = ("selectedissue", "issuekey", "issue")


def _key_from_url(s: str) -> str | None:
    """Pull an issue key from a JIRA URL's query params or ``/browse/`` path."""
    params = {k.lower(): v for k, v in parse_qs(urlparse(s).query).items()}
    for name in _KEY_PARAMS:
        for val in params.get(name, []):
            m = _ISSUE_KEY_RE.search(val)
            if m:
                return m.group(0).upper()
    m = _BROWSE_RE.search(s)
    return m.group(1).upper() if m else None


def normalize_issue_key(raw: str) -> str:
    """Extract a JIRA issue key (e.g. ``MAV-26``) from arbitrary user input.

    Accepts a bare key (``MAV-26`` / ``mav-26``) or a pasted JIRA URL such as
    ``.../browse/MAV-26`` or ``...?selectedIssue=MAV-26`` (any casing). Returns
    the upper-cased key. Raises ``ValueError`` when no key can be found.
    """
    s = (raw or "").strip()
    if not s:
        raise ValueError("No issue key provided.")

    # Fast path: the input is already exactly a key.
    if _FULL_KEY_RE.match(s):
        return s.upper()

    # Structured extraction for pasted URLs (more reliable than a blind scan).
    if "://" in s or "/" in s or "?" in s:
        found = _key_from_url(s)
        if found:
            return found

    # Fallback: first key-like token anywhere in the string.
    m = _ISSUE_KEY_RE.search(s)
    if m:
        return m.group(0).upper()
    raise ValueError(f"No JIRA issue key found in '{raw}'. Use a key like PROJ-123.")


# --------------------------------------------------------------------------- #
# stories.json  <->  StoryBundle
# --------------------------------------------------------------------------- #
def parse_story_bundle(content: str | dict) -> StoryBundle:
    """Parse a ``stories.json`` artifact (string or dict) into a StoryBundle.

    Tolerant of a bare list of stories or a ``{epic, stories}`` object.
    """
    data = content
    if isinstance(content, str):
        data = json.loads(content)
    if isinstance(data, list):
        data = {"stories": data}
    return StoryBundle.model_validate(data)


# --------------------------------------------------------------------------- #
# Atlassian Document Format (ADF) — minimal builder + flattener
# --------------------------------------------------------------------------- #
def _text(s: str) -> dict:
    return {"type": "text", "text": s}


def build_adf(description: str, acceptance_criteria: List[str]) -> dict:
    """Build a minimal ADF document for an issue description (API v3)."""
    content: List[dict] = []
    if description:
        content.append({"type": "paragraph", "content": [_text(description)]})
    if acceptance_criteria:
        content.append(
            {"type": "heading", "attrs": {"level": 3}, "content": [_text("Acceptance Criteria")]}
        )
        content.append(
            {
                "type": "bulletList",
                "content": [
                    {"type": "listItem", "content": [{"type": "paragraph", "content": [_text(ac)]}]}
                    for ac in acceptance_criteria
                ],
            }
        )
    if not content:  # ADF requires at least one node
        content.append({"type": "paragraph", "content": [_text("")]})
    return {"type": "doc", "version": 1, "content": content}


def flatten_adf(node: dict | None) -> str:
    """Flatten an ADF document (or any node) into readable plain text."""
    if not node or not isinstance(node, dict):
        return ""
    parts: List[str] = []

    def walk(n: dict) -> None:
        if not isinstance(n, dict):
            return
        ntype = n.get("type")
        if ntype == "text":
            parts.append(n.get("text", ""))
        children = n.get("content") or []
        for child in children:
            walk(child)
        # Block-level separators for readability.
        if ntype in {"paragraph", "heading", "listItem"}:
            parts.append("\n")

    walk(node)
    text = "".join(parts)
    # Collapse excessive blank lines.
    lines = [ln.rstrip() for ln in text.splitlines()]
    out: List[str] = []
    for ln in lines:
        if ln or (out and out[-1]):
            out.append(ln)
    return "\n".join(out).strip()


# --------------------------------------------------------------------------- #
# Story -> JIRA fields
# --------------------------------------------------------------------------- #
def story_to_fields(
    story: Story,
    *,
    project_key: str,
    parent_key: str | None = None,
    story_points_field: str = "",
    marker_label: str = "sdlc-agent",
    assignee_account_id: str | None = None,
) -> dict:
    """Build the ``fields`` payload for ``POST /rest/api/3/issue``."""
    labels = [l.replace(" ", "-") for l in story.labels]
    if marker_label and marker_label not in labels:
        labels.append(marker_label)
    fields: dict = {
        "project": {"key": project_key},
        "summary": story.summary[:255],
        "issuetype": {"name": story.issue_type or "Story"},
        "description": build_adf(story.description, story.acceptance_criteria),
        "labels": labels,
    }
    if parent_key:
        fields["parent"] = {"key": parent_key}
    if story_points_field and story.story_points is not None:
        fields[story_points_field] = story.story_points
    if assignee_account_id:
        fields["assignee"] = {"accountId": assignee_account_id}
    return fields


def subtask_to_fields(
    subtask: Subtask,
    *,
    project_key: str,
    parent_key: str,
    subtask_type: str = "Sub-task",
    assignee_account_id: str | None = None,
) -> dict:
    """Build the ``fields`` payload for a Sub-task (must reference its parent Story)."""
    fields: dict = {
        "project": {"key": project_key},
        "summary": subtask.summary[:255],
        "issuetype": {"name": subtask_type},
        "parent": {"key": parent_key},
        "description": build_adf(subtask.description, []),
    }
    if assignee_account_id:
        fields["assignee"] = {"accountId": assignee_account_id}
    return fields


# --------------------------------------------------------------------------- #
# JiraIssue -> pipeline feature-request string (inbound)
# --------------------------------------------------------------------------- #
def issue_to_feature_request(issue: JiraIssue) -> str:
    """Turn a fetched issue into the plain-text request the pipeline consumes."""
    lines: List[str] = [issue.summary.strip()]
    if issue.description_text.strip():
        lines += ["", issue.description_text.strip()]
    if issue.acceptance_criteria:
        lines += ["", "Acceptance Criteria:"]
        lines += [f"- {ac}" for ac in issue.acceptance_criteria]
    if issue.children:
        lines += ["", "Child stories:"]
        lines += [f"- {c.summary}" for c in issue.children]
    return "\n".join(lines).strip()

