"""Abstract JIRA client contract (mirrors ``llm/base.py``)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from .models import CreatedIssue, Epic, JiraIssue, Story


class JiraClient(ABC):
    name: str = "base"
    # Human-readable label shown in the UI badge (e.g. "Mock (free)").
    label: str = "Base"

    # --- inbound (read) ---
    @abstractmethod
    async def get_issue(self, key: str) -> JiraIssue:
        """Fetch a single issue (with children, if any)."""
        raise NotImplementedError

    @abstractmethod
    async def search(self, jql: str, *, limit: int = 50) -> List[JiraIssue]:
        """Run a JQL search (used for epic children, dedupe, etc.)."""
        raise NotImplementedError

    @abstractmethod
    async def list_projects(self) -> List[dict]:
        raise NotImplementedError

    # --- outbound (write) ---
    @abstractmethod
    async def create_epic(self, epic: Epic) -> CreatedIssue:
        raise NotImplementedError

    @abstractmethod
    async def create_issue(self, story: Story, *, parent_key: Optional[str] = None) -> CreatedIssue:
        raise NotImplementedError

    async def bulk_create(
        self, stories: List[Story], *, parent_key: Optional[str] = None
    ) -> List[CreatedIssue]:
        """Default: create stories one-by-one. Real client may batch."""
        created: List[CreatedIssue] = []
        for story in stories:
            created.append(await self.create_issue(story, parent_key=parent_key))
        return created

