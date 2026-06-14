"""Real GitHub client (used when ``GITHUB_PROVIDER=cloud``).

Talks to the GitHub REST API over HTTPS with a token (fine-grained PAT), using
the same lazy/robust style as ``jira/cloud.py`` and reusing the shared OS
trust-store TLS helper (``net.py``) for corporate HTTPS inspection.

Safety/robustness:
- ``GITHUB_DRY_RUN=true`` → never writes; returns plausible simulated results.
- Retries 429 / 5xx with backoff, honoring ``Retry-After``.
- Surfaces GitHub error bodies as clean ``RuntimeError`` (router maps to 502).
- The token is never logged or returned to callers.
- Writes only ever go to a NEW branch + PR (existing repo) or a fresh repo —
  never a force-push to an existing default branch.
"""
from __future__ import annotations

import asyncio
import base64
import logging
from typing import Any, List, Optional

import httpx

from ...net import build_ssl_verify
from .base import GitHubClient
from .models import GitHubIssue, PullRequest, RepoFile, RepoRef

logger = logging.getLogger("sdlc.github")

_API_VERSION = "2022-11-28"
_USER_REPOS = "/user/repos"  # create repo (POST) / list repos (GET) for the authed user


class CloudGitHubClient(GitHubClient):
    name = "cloud"
    label = "GitHub"

    def __init__(self, settings: Any, *, transport: Optional[httpx.BaseTransport] = None) -> None:
        super().__init__(settings.github_repo or "", owner=getattr(settings, "github_owner", ""))
        self._api = (settings.github_api_url or "https://api.github.com").rstrip("/")
        self._token = settings.github_token
        self._default_branch = settings.github_default_branch or "main"
        self._private = bool(getattr(settings, "github_private", True))
        self._dry_run = bool(getattr(settings, "github_dry_run", False))
        self._transport = transport
        self._verify = build_ssl_verify(
            getattr(settings, "github_ca_bundle", "") or "",
            getattr(settings, "github_verify_ssl", True),
        )
        self._timeout = httpx.Timeout(30.0)
        self._max_retries = 3
        self._backoff = 0.5
        self._login: Optional[str] = None  # authenticated user (lazy, cached)
        target = self.repo if self.has_default_repo else (self.owner or "?")
        self.label = f"GitHub · {target}" + (" (dry-run)" if self._dry_run else "")

    # ------------------------------------------------------------------ #
    # HTTP plumbing
    # ------------------------------------------------------------------ #
    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._api,
            timeout=self._timeout,
            transport=self._transport,
            verify=self._verify,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": _API_VERSION,
            },
        )

    async def _request(self, http: httpx.AsyncClient, method: str, path: str, **kw: Any) -> httpx.Response:
        resp: Optional[httpx.Response] = None
        for attempt in range(self._max_retries + 1):
            resp = await http.request(method, path, **kw)
            transient = resp.status_code == 429 or resp.status_code >= 500
            if transient and attempt < self._max_retries:
                retry_after = resp.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else self._backoff * (2 ** attempt)
                logger.warning("GitHub %s %s -> %s; retry in %.1fs (%d/%d)",
                               method, path, resp.status_code, delay, attempt + 1, self._max_retries)
                await asyncio.sleep(min(delay, 10.0))
                continue
            return resp
        assert resp is not None
        return resp

    @staticmethod
    def _token_hint(resp: httpx.Response) -> str:
        """Operation-specific guidance for the common token-scope 403."""
        try:
            path = resp.request.url.path
        except Exception:  # noqa: BLE001 — best-effort only
            path = ""
        if path.endswith(_USER_REPOS):
            return (
                " — your token can't CREATE repositories. A token scoped to a single "
                "repo cannot create new ones. Use a fine-grained token with Repository "
                "access = 'All repositories' and 'Administration: Read and write' + "
                "'Contents: Read and write', or a classic token with the 'repo' scope."
            )
        if "/pulls" in path:
            return " — grant the token 'Pull requests: Read and write' for this repo."
        if "/contents/" in path or "/git/" in path:
            return (
                " — grant 'Contents: Read and write' and make sure the token has access "
                "to this repository (or set Repository access = 'All repositories')."
            )
        return (
            " — the token lacks permission for this action. Review its repository access "
            "and permissions (Administration / Contents / Pull requests)."
        )

    @classmethod
    def _error(cls, resp: httpx.Response) -> str:
        detail = resp.text
        try:
            body = resp.json()
            detail = body.get("message") or resp.text
            if body.get("errors"):
                detail += " — " + "; ".join(str(e) for e in body["errors"])
        except Exception:  # noqa: BLE001
            pass
        msg = f"GitHub {resp.status_code}: {detail}"[:300]
        low = detail.lower()
        if resp.status_code == 403 and (
            "network administrator has blocked" in low or "only tokens for the" in low
        ):
            msg += (
                " — NOTE: this is a corporate NETWORK block, not a token problem. Your "
                "request reached GitHub but the network only allows enterprise tokens. "
                "Run off this network (or the hosted demo), or switch GitHub to Mock mode."
            )
        elif resp.status_code == 403 and (
            "not accessible by personal access token" in low or "resource not accessible" in low
        ):
            msg += cls._token_hint(resp)
        elif resp.status_code == 401:
            msg += " — check GITHUB_TOKEN in .env.local (it may be wrong or expired)."
        return msg

    def _json_or_raise(self, resp: httpx.Response) -> dict:
        if resp.status_code >= 400:
            raise RuntimeError(self._error(resp))
        return resp.json() if resp.content else {}

    # ------------------------------------------------------------------ #
    # Primitives
    # ------------------------------------------------------------------ #
    async def repo_exists(self, repo: str) -> bool:
        async with self._client() as http:
            resp = await self._request(http, "GET", f"/repos/{repo}")
        if resp.status_code == 404:
            return False
        if resp.status_code >= 400:
            raise RuntimeError(self._error(resp))
        return True

    async def _whoami(self, http: httpx.AsyncClient) -> str:
        """Return the authenticated user's login (cached); '' if unknown."""
        if self._login is not None:
            return self._login
        resp = await self._request(http, "GET", "/user")
        self._login = (resp.json() or {}).get("login", "") if resp.status_code < 400 else ""
        return self._login

    async def create_repo(self, repo: str, *, private: bool = True, description: str = "") -> RepoRef:
        owner, name = self._split(repo)
        if self._dry_run:
            return RepoRef(owner=owner, name=name, default_branch=self._default_branch,
                           url=self._url_for(repo))
        payload = {"name": name, "private": bool(private), "auto_init": True,
                   "description": description or "Generated by SDLC Agentic AI"}
        async with self._client() as http:
            login = await self._whoami(http)
            # POST /user/repos creates under the authenticated account; for a
            # different owner (an org), POST /orgs/{owner}/repos is required.
            if owner and login and owner.lower() != login.lower():
                path = f"/orgs/{owner}/repos"
            else:
                path = _USER_REPOS
            try:
                data = self._json_or_raise(await self._request(http, "POST", path, json=payload))
            except RuntimeError as exc:
                raise self._create_repo_error(exc, owner=owner, login=login, path=path) from exc
        full = data.get("full_name") or repo
        f_owner, f_name = self._split(full)
        return RepoRef(owner=f_owner, name=f_name,
                       default_branch=data.get("default_branch", self._default_branch),
                       url=data.get("html_url", self._url_for(full)))

    @staticmethod
    def _create_repo_error(exc: RuntimeError, *, owner: str, login: str, path: str) -> RuntimeError:
        """Enrich a repo-creation failure with owner/token context."""
        msg = str(exc)
        if "403" not in msg and "404" not in msg:
            return exc
        if login and owner and owner.lower() != login.lower():
            kind = "organization" if path.startswith("/orgs/") else "account"
            return RuntimeError(
                f"{msg} Your token authenticates as '{login}', but the target {kind} is "
                f"'{owner}'. Set GITHUB_OWNER to '{login}', or use a token that can create "
                f"repos in '{owner}' (org members need 'Administration: Read and write')."
            )
        return exc

    async def get_default_branch(self, repo: str) -> str:
        async with self._client() as http:
            data = self._json_or_raise(await self._request(http, "GET", f"/repos/{repo}"))
        return data.get("default_branch", self._default_branch)

    async def _branch_sha(self, http: httpx.AsyncClient, repo: str, branch: str) -> str:
        data = self._json_or_raise(
            await self._request(http, "GET", f"/repos/{repo}/git/ref/heads/{branch}")
        )
        return data.get("object", {}).get("sha", "")

    async def create_branch(self, repo: str, branch: str, *, from_branch: str) -> str:
        if self._dry_run:
            return branch
        async with self._client() as http:
            sha = await self._branch_sha(http, repo, from_branch)
            payload = {"ref": f"refs/heads/{branch}", "sha": sha}
            self._json_or_raise(await self._request(http, "POST", f"/repos/{repo}/git/refs", json=payload))
        return branch

    async def _file_sha(self, http: httpx.AsyncClient, repo: str, path: str, branch: str) -> str:
        resp = await self._request(http, "GET", f"/repos/{repo}/contents/{path}", params={"ref": branch})
        if resp.status_code == 200:
            return resp.json().get("sha", "")
        return ""

    async def commit_files(self, repo: str, files: List[RepoFile], *, branch: str, message: str) -> int:
        if self._dry_run:
            return len(files)
        count = 0
        async with self._client() as http:
            for f in files:
                b64 = base64.b64encode(f.content.encode("utf-8")).decode("ascii")
                payload: dict = {"message": f"{message}: {f.path}", "content": b64, "branch": branch}
                sha = await self._file_sha(http, repo, f.path, branch)
                if sha:
                    payload["sha"] = sha
                self._json_or_raise(
                    await self._request(http, "PUT", f"/repos/{repo}/contents/{f.path}", json=payload)
                )
                count += 1
        return count

    async def open_pull_request(self, repo: str, *, head: str, base: str, title: str, body: str) -> PullRequest:
        if self._dry_run:
            return PullRequest(number=0, url=f"{self._url_for(repo)}/pull/0", branch=head, base=base, title=title)
        payload = {"title": title, "head": head, "base": base, "body": body}
        async with self._client() as http:
            data = self._json_or_raise(await self._request(http, "POST", f"/repos/{repo}/pulls", json=payload))
        return PullRequest(number=data.get("number", 0), url=data.get("html_url", f"{self._url_for(repo)}/pulls"),
                           branch=head, base=base, title=title)

    async def get_issue(self, number: int, *, repo: Optional[str] = None) -> GitHubIssue:
        repo = repo or self.repo
        async with self._client() as http:
            data = self._json_or_raise(await self._request(http, "GET", f"/repos/{repo}/issues/{number}"))
        return GitHubIssue(
            number=data.get("number", number),
            title=data.get("title", ""),
            body=data.get("body") or "",
            labels=[l.get("name", "") for l in data.get("labels", []) if isinstance(l, dict)],
            url=data.get("html_url", f"{self._url_for(repo)}/issues/{number}"),
        )

    async def list_repos(self) -> List[str]:
        async with self._client() as http:
            data = self._json_or_raise(
                await self._request(http, "GET", _USER_REPOS,
                                    params={"per_page": 100, "sort": "updated"})
            )
        if not isinstance(data, list):
            return []
        return [r.get("full_name") for r in data if isinstance(r, dict) and r.get("full_name")]

    async def get_repo_tree(self, repo: str, *, branch: Optional[str] = None) -> List[str]:
        branch = branch or await self.get_default_branch(repo)
        async with self._client() as http:
            data = self._json_or_raise(
                await self._request(http, "GET", f"/repos/{repo}/git/trees/{branch}",
                                    params={"recursive": "1"})
            )
        tree = data.get("tree", []) if isinstance(data, dict) else []
        return [t.get("path", "") for t in tree if isinstance(t, dict) and t.get("type") == "blob"]

    async def get_file(self, repo: str, path: str, *, branch: Optional[str] = None) -> RepoFile:
        params = {"ref": branch} if branch else None
        async with self._client() as http:
            data = self._json_or_raise(
                await self._request(http, "GET", f"/repos/{repo}/contents/{path}", params=params)
            )
        content = ""
        if isinstance(data, dict) and data.get("encoding") == "base64" and data.get("content"):
            try:
                content = base64.b64decode(data["content"]).decode("utf-8")
            except ValueError:  # bad base64 / non-UTF-8 (UnicodeDecodeError is a ValueError)
                content = ""  # binary/non-UTF-8 — treated as skippable by the caller
        return RepoFile(path=path, content=content, sha=data.get("sha", "") if isinstance(data, dict) else "")

    async def diagnose(self) -> dict:
        """Probe the token (GET /user) and report what it can do — never leaks it.

        Helps debug 403s: confirms auth, the authenticated login, whether it
        matches the configured owner, and (for classic tokens) the scopes so the
        UI can say whether the token can create repositories.
        """
        async with self._client() as http:
            resp = await self._request(http, "GET", "/user")
            if resp.status_code >= 400:
                raise RuntimeError(self._error(resp))
            body = resp.json() or {}
            raw_scopes = resp.headers.get("x-oauth-scopes")  # present for classic tokens only
        login = body.get("login", "") or ""
        self._login = login
        token_type = "classic" if raw_scopes is not None else "fine-grained"
        scopes = [s.strip() for s in raw_scopes.split(",") if s.strip()] if raw_scopes else []
        # Classic: 'repo' (or 'public_repo') allows creation. Fine-grained scopes
        # aren't exposed via the API, so we can't assert capability (-> None).
        can_create: Optional[bool] = None
        if token_type == "classic":
            can_create = "repo" in scopes or "public_repo" in scopes
        owner = self.owner
        owner_matches = (not owner) or (login.lower() == owner.lower())
        return {
            "provider": self.name,
            "authenticated_as": login,
            "configured_owner": owner,
            "owner_matches": owner_matches,
            "token_type": token_type,
            "scopes": scopes,
            "can_create_repos": can_create,
            "has_default_repo": self.has_default_repo,
            "default_repo": self.repo if self.has_default_repo else None,
        }

