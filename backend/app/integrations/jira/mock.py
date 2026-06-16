"""Free, offline, in-memory JIRA client — the default provider.

Returns realistic issue keys (``DEMO-123``) and stores created issues so the
whole feature is demoable with **zero JIRA account**, mirroring the mock LLM
provider. Also seeds a demo Epic + child stories so inbound *import* works
offline too.
"""
from __future__ import annotations

from typing import List, Optional

from .base import JiraClient
from .models import CreatedIssue, Epic, JiraIssue, Story, Subtask

_DEMO_HOST = "https://demo.atlassian.net"


class MockJiraClient(JiraClient):
    name = "mock"
    label = "Mock (free)"

    def __init__(self, base_url: str = "", project_key: str = "DEMO", default_assignee: str = "") -> None:
        self._host = (base_url or _DEMO_HOST).rstrip("/")
        self._project = project_key or "DEMO"
        self._default_assignee = default_assignee or ""
        self._counter = 100  # created issues start at DEMO-101
        self._created: dict[str, CreatedIssue] = {}
        self._seed()

    # ------------------------------------------------------------------ #
    def _url(self, key: str) -> str:
        return f"{self._host}/browse/{key}"

    def _seed(self) -> None:
        """Seed a demo Epic (DEMO-1) with two child stories for inbound import."""
        self._issues: dict[str, JiraIssue] = {
            f"{self._project}-2": JiraIssue(
                key=f"{self._project}-2",
                summary="Sign in with email and password",
                description_text="As a user, I can sign in with my email and password.",
                issue_type="Story",
                acceptance_criteria=["Email must be valid", "401 on bad credentials"],
            ),
            f"{self._project}-3": JiraIssue(
                key=f"{self._project}-3",
                summary="Show validation errors",
                description_text="As a user, I see clear validation errors on bad input.",
                issue_type="Story",
                acceptance_criteria=["Inline messages", "Errors announced for a11y"],
            ),
        }
        self._issues[f"{self._project}-1"] = JiraIssue(
            key=f"{self._project}-1",
            summary="Email/password login",
            description_text=(
                "Allow users to authenticate with email and password, with secure "
                "credential handling and clear error states."
            ),
            issue_type="Epic",
            acceptance_criteria=[
                "Passwords are never stored in plaintext",
                "Generic error on failed login",
            ],
            children=[self._issues[f"{self._project}-2"], self._issues[f"{self._project}-3"]],
        )

    # --- inbound ------------------------------------------------------- #
    async def get_issue(self, key: str) -> JiraIssue:
        key = key.strip().upper()
        if key in self._issues:
            return self._issues[key]
        # Synthesize a believable issue for any unknown key so demos never 404.
        return JiraIssue(
            key=key,
            summary=f"Imported issue {key}",
            description_text=f"Placeholder description for {key} (mock JIRA).",
            issue_type="Story",
            acceptance_criteria=["Acceptance criteria to be refined."],
        )

    async def search(self, jql: str, *, limit: int = 50) -> List[JiraIssue]:
        # Minimal: return seeded stories (good enough for the offline demo).
        return [i for i in self._issues.values() if i.issue_type == "Story"][:limit]

    async def list_projects(self) -> List[dict]:
        return [{"key": self._project, "name": "Demo Project"}]

    # --- outbound ------------------------------------------------------ #
    def _next_key(self) -> str:
        self._counter += 1
        return f"{self._project}-{self._counter}"

    async def create_epic(self, epic: Epic) -> CreatedIssue:
        key = self._next_key()
        created = CreatedIssue(key=key, url=self._url(key), summary=epic.summary, issue_type="Epic")
        self._created[key] = created
        return created

    @staticmethod
    def _display_assignee(spec: str) -> Optional[str]:
        if not spec:
            return None
        if spec.lower() in {"me", "self"}:
            return "Me (token owner)"
        return spec

    async def create_issue(self, story: Story, *, parent_key: Optional[str] = None) -> CreatedIssue:
        spec = (story.assignee or self._default_assignee or "").strip()
        assignee = self._display_assignee(spec)

        key = self._next_key()
        created = CreatedIssue(
            key=key,
            url=self._url(key),
            summary=story.summary,
            issue_type=story.issue_type or "Story",
            assignee=assignee,
        )
        # Create sub-tasks under this story (mirrors the real client).
        for sub in story.subtasks:
            sub_key = self._next_key()
            created.subtasks.append(
                CreatedIssue(
                    key=sub_key,
                    url=self._url(sub_key),
                    summary=sub.summary,
                    issue_type="Sub-task",
                    assignee=assignee,
                )
            )
        self._created[key] = created
        return created

    async def update_issue(
        self,
        key: str,
        *,
        summary: Optional[str] = None,
        description: str = "",
        acceptance_criteria: Optional[List[str]] = None,
    ) -> CreatedIssue:
        key = key.strip().upper()
        existing = self._issues.get(key)
        if existing is not None:
            if summary:
                existing.summary = summary
            if description:
                existing.description_text = description
            if acceptance_criteria:
                existing.acceptance_criteria = acceptance_criteria
        return CreatedIssue(
            key=key,
            url=self._url(key),
            summary=summary or (existing.summary if existing else key),
            issue_type=(existing.issue_type if existing else "Epic"),
        )

    async def create_subtask(self, subtask: Subtask, *, parent_key: str) -> CreatedIssue:
        key = self._next_key()
        created = CreatedIssue(
            key=key,
            url=self._url(key),
            summary=subtask.summary,
            issue_type="Sub-task",
            assignee=self._display_assignee(self._default_assignee),
        )
        self._created[key] = created
        return created

