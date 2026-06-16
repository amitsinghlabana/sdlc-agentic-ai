"""Real JIRA Cloud client (used when ``JIRA_PROVIDER=cloud``).

Talks to the JIRA Cloud REST API **v3** over HTTPS with API-token Basic auth,
mirroring the lazy-import style of ``llm/azure_openai.py``. Reuses the shared
ADF + field mapping helpers in ``mapping.py`` so the logic stays testable.

Safety/robustness:
- ``JIRA_DRY_RUN=true`` → never POSTs; returns what it *would* create.
- Retries 429 / 5xx with backoff, honoring ``Retry-After``.
- Surfaces JIRA error bodies as clean ``RuntimeError`` (the router maps to 502).
- The token is never logged or returned to callers.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, List, Optional
from urllib.parse import urlparse

import httpx

from ...net import build_ssl_verify
from .base import JiraClient
from .mapping import build_adf, flatten_adf, story_to_fields, subtask_to_fields
from .models import CreatedIssue, Epic, JiraIssue, Story, Subtask

logger = logging.getLogger("sdlc.jira")

# Fields we request when reading an issue (keep minimal to limit payload).
_ISSUE_FIELDS = "summary,description,issuetype,labels,subtasks,parent"
_SEARCH_FIELDS = ["summary", "description", "issuetype", "labels"]


def _build_verify(settings: Any):
    """JIRA TLS verify strategy (delegates to the shared helper)."""
    return build_ssl_verify(
        getattr(settings, "jira_ca_bundle", "") or "",
        getattr(settings, "jira_verify_ssl", True),
    )


class CloudJiraClient(JiraClient):
    name = "cloud"
    label = "JIRA Cloud"

    def __init__(self, settings: Any, *, transport: Optional[httpx.BaseTransport] = None) -> None:
        self._base = settings.jira_base_url.rstrip("/")
        self._api_root = f"{self._base}/rest/api/3"
        self._email = settings.jira_email
        self._token = settings.jira_api_token
        self._project = settings.jira_project_key or "SDLC"
        self._sp_field = settings.jira_story_points_field
        self._default_assignee = getattr(settings, "jira_default_assignee", "") or ""
        self._subtask_type = getattr(settings, "jira_subtask_issue_type", "") or "Sub-task"
        self._dry_run = bool(settings.jira_dry_run)
        # Injected by tests (httpx.MockTransport); None in production.
        self._transport = transport
        # TLS verify strategy (OS trust store / custom CA / disabled).
        self._verify = _build_verify(settings)
        # Cache of assignee spec -> accountId (avoid repeated lookups per run).
        self._account_cache: dict[str, Optional[str]] = {}

        self._timeout = httpx.Timeout(30.0)
        self._max_retries = 3
        self._backoff = 0.5  # seconds (base for exponential backoff)

        host = urlparse(self._base).netloc or self._base
        self.label = f"JIRA Cloud · {host}" + (" (dry-run)" if self._dry_run else "")

    # ------------------------------------------------------------------ #
    # HTTP plumbing
    # ------------------------------------------------------------------ #
    def _client(self) -> httpx.AsyncClient:
        """A fresh auth'd client per call (safe with FastAPI's per-request loop)."""
        return httpx.AsyncClient(
            base_url=self._api_root,
            auth=(self._email, self._token),
            timeout=self._timeout,
            transport=self._transport,
            verify=self._verify,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

    def _browse(self, key: str) -> str:
        return f"{self._base}/browse/{key}"

    async def _request(self, http: httpx.AsyncClient, method: str, path: str, **kw: Any) -> httpx.Response:
        """Send a request, retrying transient 429/5xx with backoff."""
        resp: Optional[httpx.Response] = None
        for attempt in range(self._max_retries + 1):
            resp = await http.request(method, path, **kw)
            transient = resp.status_code == 429 or resp.status_code >= 500
            if transient and attempt < self._max_retries:
                retry_after = resp.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else self._backoff * (2 ** attempt)
                logger.warning(
                    "JIRA %s %s -> %s; retrying in %.1fs (attempt %d/%d)",
                    method, path, resp.status_code, delay, attempt + 1, self._max_retries,
                )
                await asyncio.sleep(min(delay, 10.0))
                continue
            return resp
        assert resp is not None
        return resp

    def _json_or_raise(self, resp: httpx.Response) -> dict:
        if resp.status_code >= 400:
            raise RuntimeError(self._error_message(resp))
        if not resp.content:
            return {}
        return resp.json()

    @staticmethod
    def _error_message(resp: httpx.Response) -> str:
        detail = resp.text
        try:
            body = resp.json()
            msgs = body.get("errorMessages") or []
            errs = body.get("errors") or {}
            detail = "; ".join(msgs) or "; ".join(f"{k}: {v}" for k, v in errs.items()) or resp.text
        except Exception:  # noqa: BLE001 — non-JSON error body
            pass
        return f"JIRA {resp.status_code}: {detail}"[:500]

    async def _get_json(self, http: httpx.AsyncClient, path: str, **kw: Any) -> dict:
        return self._json_or_raise(await self._request(http, "GET", path, **kw))

    async def _post_json(self, http: httpx.AsyncClient, path: str, **kw: Any) -> dict:
        return self._json_or_raise(await self._request(http, "POST", path, **kw))

    async def _put(self, http: httpx.AsyncClient, path: str, **kw: Any) -> None:
        """Send a PUT (e.g. issue update); raise on error. Returns no body (204)."""
        resp = await self._request(http, "PUT", path, **kw)
        if resp.status_code >= 400:
            raise RuntimeError(self._error_message(resp))

    # ------------------------------------------------------------------ #
    # Inbound (read)
    # ------------------------------------------------------------------ #
    def _issue_from_raw(self, raw: dict) -> JiraIssue:
        fields = raw.get("fields") or {}
        issue_type = ((fields.get("issuetype") or {}).get("name")) or "Story"
        children: List[JiraIssue] = []
        for sub in fields.get("subtasks") or []:
            sub_fields = sub.get("fields") or {}
            children.append(
                JiraIssue(
                    key=sub.get("key", ""),
                    summary=sub_fields.get("summary", ""),
                    issue_type=((sub_fields.get("issuetype") or {}).get("name")) or "Sub-task",
                )
            )
        return JiraIssue(
            key=raw.get("key", ""),
            summary=fields.get("summary", "") or "",
            description_text=flatten_adf(fields.get("description")),
            issue_type=issue_type,
            labels=fields.get("labels") or [],
            children=children,
        )

    async def get_issue(self, key: str) -> JiraIssue:
        key = key.strip().upper()
        async with self._client() as http:
            raw = await self._get_json(http, f"/issue/{key}", params={"fields": _ISSUE_FIELDS})
        issue = self._issue_from_raw(raw)
        # For an Epic, gather child stories via JQL (team-managed `parent`).
        if issue.issue_type.lower() == "epic" and not issue.children:
            try:
                issue.children = await self.search(f'parent = "{key}" ORDER BY created ASC', limit=50)
            except Exception:  # noqa: BLE001 — children are best-effort
                logger.warning("Could not fetch children for epic %s", key, exc_info=True)
        return issue

    async def search(self, jql: str, *, limit: int = 50) -> List[JiraIssue]:
        body = {"jql": jql, "maxResults": limit, "fields": _SEARCH_FIELDS}
        async with self._client() as http:
            data = await self._post_json(http, "/search/jql", json=body)
        return [self._issue_from_raw(i) for i in data.get("issues", [])]

    async def list_projects(self) -> List[dict]:
        async with self._client() as http:
            data = await self._get_json(http, "/project/search", params={"maxResults": 50})
        return [{"key": p.get("key", ""), "name": p.get("name", "")} for p in data.get("values", [])]

    # ------------------------------------------------------------------ #
    # User / assignee resolution
    # ------------------------------------------------------------------ #
    @staticmethod
    def _display_assignee(spec: str) -> Optional[str]:
        if not spec:
            return None
        if spec.lower() in {"me", "self"}:
            return "Me (token owner)"
        return spec  # email or accountId

    async def _resolve_account_id(self, spec: str) -> Optional[str]:
        """Resolve an assignee spec ("me"/email/accountId) to a JIRA accountId.

        Cloud requires ``accountId`` (not username/email) on the assignee field.
        Results are cached per spec for the life of the client.
        """
        spec = (spec or "").strip()
        if not spec:
            return None
        if spec in self._account_cache:
            return self._account_cache[spec]

        account_id: Optional[str] = None
        try:
            async with self._client() as http:
                if spec.lower() in {"me", "self"}:
                    data = await self._get_json(http, "/myself")
                    account_id = data.get("accountId")
                elif "@" in spec:
                    users = self._json_or_raise(
                        await self._request(http, "GET", "/user/search", params={"query": spec})
                    )
                    if isinstance(users, list) and users:
                        account_id = users[0].get("accountId")
                else:
                    account_id = spec  # assume it's already an accountId
        except Exception:  # noqa: BLE001 — assignment is best-effort, never fatal
            logger.warning("Could not resolve assignee %r; leaving unassigned.", spec, exc_info=True)
            account_id = None

        self._account_cache[spec] = account_id
        return account_id

    # ------------------------------------------------------------------ #
    # Outbound (write)
    # ------------------------------------------------------------------ #
    async def _create(self, fields: dict, *, summary: str, issue_type: str) -> CreatedIssue:
        if self._dry_run:
            logger.info("[DRY-RUN] would create %s in %s: %s", issue_type, self._project, summary)
            key = f"{self._project}-DRYRUN"
            return CreatedIssue(key=key, url=self._browse(key), summary=summary, issue_type=issue_type)
        async with self._client() as http:
            data = await self._post_json(http, "/issue", json={"fields": fields})
        key = data.get("key", "")
        return CreatedIssue(key=key, url=self._browse(key), summary=summary, issue_type=issue_type)

    async def create_epic(self, epic: Epic) -> CreatedIssue:
        fields = {
            "project": {"key": self._project},
            "summary": epic.summary[:255],
            "issuetype": {"name": "Epic"},
            "description": build_adf(epic.description, []),
        }
        return await self._create(fields, summary=epic.summary, issue_type="Epic")

    async def create_issue(self, story: Story, *, parent_key: Optional[str] = None) -> CreatedIssue:
        # Resolve assignee (per-story override, else the configured default).
        spec = (story.assignee or self._default_assignee or "").strip()
        account_id = None if self._dry_run else await self._resolve_account_id(spec)

        fields = story_to_fields(
            story,
            project_key=self._project,
            parent_key=parent_key,
            story_points_field=self._sp_field,
            assignee_account_id=account_id,
        )
        created = await self._create(fields, summary=story.summary, issue_type=story.issue_type or "Story")
        created.assignee = self._display_assignee(spec)

        # Create sub-tasks under the freshly-created story (parent = story key).
        for sub in story.subtasks:
            sub_fields = subtask_to_fields(
                sub,
                project_key=self._project,
                parent_key=created.key,
                subtask_type=self._subtask_type,
                assignee_account_id=account_id,  # inherit the story's assignee
            )
            sub_created = await self._create(sub_fields, summary=sub.summary, issue_type=self._subtask_type)
            sub_created.assignee = created.assignee
            created.subtasks.append(sub_created)

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
        fields: dict = {}
        if summary:
            fields["summary"] = summary[:255]
        if description or acceptance_criteria:
            fields["description"] = build_adf(description, acceptance_criteria or [])

        if fields and not self._dry_run:
            async with self._client() as http:
                await self._put(http, f"/issue/{key}", json={"fields": fields})
        elif self._dry_run:
            logger.info("[DRY-RUN] would update %s: %s", key, ", ".join(fields) or "(no changes)")

        return CreatedIssue(
            key=key, url=self._browse(key), summary=summary or key, issue_type="Epic"
        )

    async def create_subtask(self, subtask: Subtask, *, parent_key: str) -> CreatedIssue:
        account_id = None if self._dry_run else await self._resolve_account_id(self._default_assignee)
        fields = subtask_to_fields(
            subtask,
            project_key=self._project,
            parent_key=parent_key,
            subtask_type=self._subtask_type,
            assignee_account_id=account_id,
        )
        created = await self._create(fields, summary=subtask.summary, issue_type=self._subtask_type)
        created.assignee = self._display_assignee(self._default_assignee)
        return created

