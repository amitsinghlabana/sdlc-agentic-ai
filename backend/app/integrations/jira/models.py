"""Pydantic models for JIRA integration (provider-agnostic)."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Subtask(BaseModel):
    """A small task that lives *under* a Story (JIRA issue type 'Sub-task')."""

    summary: str
    description: str = ""


class Story(BaseModel):
    """A single user story the Requirements agent wants to push to JIRA."""

    summary: str
    description: str = ""
    acceptance_criteria: List[str] = Field(default_factory=list)
    story_points: Optional[int] = None
    labels: List[str] = Field(default_factory=list)
    issue_type: str = "Story"
    subtasks: List[Subtask] = Field(default_factory=list)
    # Optional per-story assignee: "me"/"self", an email, or an accountId.
    assignee: Optional[str] = None


class Epic(BaseModel):
    summary: str
    description: str = ""


class StoryBundle(BaseModel):
    """The structured ``stories.json`` artifact: an optional epic + stories."""

    epic: Optional[Epic] = None
    stories: List[Story] = Field(default_factory=list)


class JiraIssue(BaseModel):
    """A JIRA issue fetched for inbound import."""

    key: str
    summary: str = ""
    description_text: str = ""
    issue_type: str = "Story"
    labels: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    children: List["JiraIssue"] = Field(default_factory=list)


class CreatedIssue(BaseModel):
    """Result of creating an issue (mock or real)."""

    key: str
    url: str
    summary: str
    issue_type: str = "Story"
    # Assignee display name (or raw value), if one was set.
    assignee: Optional[str] = None
    # Sub-tasks created under this issue.
    subtasks: List["CreatedIssue"] = Field(default_factory=list)


JiraIssue.model_rebuild()
CreatedIssue.model_rebuild()

