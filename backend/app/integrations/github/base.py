"""Abstract GitHub client contract (mirrors ``jira/base.py``).

Subclasses implement a handful of small *primitives* (repo_exists, create_repo,
create_branch, commit_files, open_pull_request, get_issue). The high-level
``publish()`` template method is shared here so both the mock and the real
client get the same two-mode behavior for free:

  * **new_repo**     — target repo doesn't exist → create it + push to default branch.
  * **pull_request** — target repo exists → new branch + commit + open a PR
    (never writes to the default branch directly).
"""
from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from typing import List, Optional

from .models import GitHubIssue, PublishResult, PullRequest, RepoFile, RepoRef


class GitHubClient(ABC):
    name: str = "base"
    label: str = "Base"

    def __init__(self, repo: str, *, owner: str = "", html_base: str = "https://github.com") -> None:
        self.repo = (repo or "").strip().strip("/")
        self._owner = (owner or "").strip().strip("/")
        self._html_base = html_base.rstrip("/")
        # Link to the default repo when fully qualified, else the owner's page.
        target = self.repo if self.has_default_repo else (self.owner or self.repo)
        self.repo_url = f"{self._html_base}/{target}" if target else self._html_base

    # --- repo identity helpers ---------------------------------------- #
    @property
    def owner(self) -> str:
        """The account/org that owns repos (explicit owner wins, else from repo)."""
        if self._owner:
            return self._owner
        return self.repo.split("/", 1)[0] if self.repo else ""

    @property
    def repo_name(self) -> str:
        return self.repo.split("/", 1)[1] if "/" in self.repo else ""

    @property
    def has_default_repo(self) -> bool:
        """True when a fully-qualified ``owner/name`` default repo is configured."""
        return bool(self.repo) and "/" in self.repo

    def _url_for(self, repo: str) -> str:
        return f"{self._html_base}/{repo}"

    @staticmethod
    def _split(repo: str) -> tuple[str, str]:
        owner, _, name = repo.partition("/")
        return owner, (name or owner)

    @staticmethod
    def _slug_repo_name(title: str) -> str:
        """Generate a repo name from the feature when none was provided."""
        slug = re.sub(r"[^a-z0-9]+", "-", (title or "app").lower()).strip("-")[:32] or "app"
        return f"sdlc-{slug}-{time.strftime('%Y%m%d-%H%M%S')}"

    def _resolve_repo(self, repo: Optional[str], *, title: str, create_new: bool) -> tuple[str, bool]:
        """Resolve the target ``owner/name`` + whether to create it.

        Accepts several shapes:
          * ``owner/name`` → that exact repo.
          * ``name`` (with a configured owner) → that repo under the owner.
          * ``owner`` only (no configured owner), or empty → no repo name, so a
            fresh repo is created (auto-named from ``title``).
        """
        raw = ((repo if repo is not None else self.repo) or "").strip().strip("/")
        if "/" in raw:
            owner, _, name = raw.partition("/")
        elif raw and self.owner and raw != self.owner:
            # A bare token + a configured owner → the token is the repo NAME.
            owner, name = self.owner, raw
        else:
            # Bare token is the owner (or empty) → no name yet → create new.
            owner, name = (raw or self.owner), ""
        if not owner:
            raise RuntimeError(
                "No GitHub owner configured — set GITHUB_OWNER (or pass 'owner/name')."
            )
        if not name:
            name = self._slug_repo_name(title)
            create_new = True  # no existing repo name → make a fresh repo
        return f"{owner}/{name}", create_new

    @staticmethod
    def _suggest_branch(title: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", (title or "feature").lower()).strip("-")[:40] or "feature"
        return f"sdlc/{slug}-{time.strftime('%H%M%S')}"

    @staticmethod
    def _pr_body(title: str, files: List[RepoFile]) -> str:
        lines = [
            f"Automated feature delivery from the **SDLC Agentic AI** pipeline: _{title}_.",
            "",
            "Generated artifacts (security-reviewed by the Reviewer agent, grounded via Foundry IQ):",
            "",
        ]
        lines += [f"- `{f.path}`" for f in files]
        lines += ["", "> Review before merging."]
        return "\n".join(lines)

    # --- primitives (implemented by subclasses) ----------------------- #
    # Each operates on an explicit ``repo`` ("owner/name") so one client can
    # target many repositories (toggle per publish).
    @abstractmethod
    async def repo_exists(self, repo: str) -> bool: ...

    @abstractmethod
    async def create_repo(self, repo: str, *, private: bool = True, description: str = "") -> RepoRef: ...

    @abstractmethod
    async def get_default_branch(self, repo: str) -> str: ...

    @abstractmethod
    async def create_branch(self, repo: str, branch: str, *, from_branch: str) -> str: ...

    @abstractmethod
    async def commit_files(self, repo: str, files: List[RepoFile], *, branch: str, message: str) -> int: ...

    @abstractmethod
    async def open_pull_request(self, repo: str, *, head: str, base: str, title: str, body: str) -> PullRequest: ...

    @abstractmethod
    async def get_issue(self, number: int, *, repo: Optional[str] = None) -> GitHubIssue: ...

    @abstractmethod
    async def list_repos(self) -> List[str]: ...

    @abstractmethod
    async def get_repo_tree(self, repo: str, *, branch: Optional[str] = None) -> List[str]: ...

    @abstractmethod
    async def get_file(self, repo: str, path: str, *, branch: Optional[str] = None) -> RepoFile: ...

    # --- diagnostics (overridable) ------------------------------------ #
    async def diagnose(self) -> dict:
        """Report token/identity info for the UI. Real clients override this to
        probe the API; the default is fine for the offline mock."""
        return {
            "provider": self.name,
            "authenticated_as": self.owner or "mock-user",
            "configured_owner": self.owner,
            "owner_matches": True,
            "token_type": self.name,
            "scopes": [],
            "can_create_repos": True,
            "has_default_repo": self.has_default_repo,
            "default_repo": self.repo if self.has_default_repo else None,
        }

    # --- existing-repo context (shared) ------------------------------- #
    # Files/dirs never loaded as context (binaries, vendored deps, lockfiles…).
    _SKIP_DIRS = (
        "node_modules/", ".git/", "dist/", "build/", ".venv/", "venv/", "__pycache__/",
        ".next/", ".turbo/", "vendor/", "coverage/", ".idea/", ".vscode/",
    )
    _SKIP_EXTS = (
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".pdf", ".zip",
        ".gz", ".tar", ".lock", ".woff", ".woff2", ".ttf", ".eot", ".map", ".min.js",
        ".pyc", ".so", ".dll", ".class", ".jar", ".mp4", ".mp3", ".bin",
    )
    _SKIP_FILES = ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock")

    @classmethod
    def _is_source_path(cls, path: str) -> bool:
        p = path.lower()
        if any(seg in p for seg in cls._SKIP_DIRS):
            return False
        if p.rsplit("/", 1)[-1] in cls._SKIP_FILES:
            return False
        return not p.endswith(cls._SKIP_EXTS)

    @staticmethod
    def _context_priority(path: str) -> tuple:
        """Sort key: prefer shallow, source-y, app files over docs/config."""
        depth = path.count("/")
        lower = path.lower()
        kind = 0 if lower.endswith((".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".java")) else 1
        return (kind, depth, path)

    async def _read_context_file(self, repo: str, path: str, branch: Optional[str]) -> Optional[RepoFile]:
        """Read one file for context, or None if unreadable/binary/too large."""
        try:
            rf = await self.get_file(repo, path, branch=branch)
        except Exception:  # skip unreadable files, keep going
            return None
        content = rf.content or ""
        if not content.strip() or len(content) > 8_000:
            return None
        return rf

    async def fetch_repo_context(
        self, repo: str, *, branch: Optional[str] = None,
        max_files: int = 12, max_bytes: int = 24_000,
    ) -> List[RepoFile]:
        """Read a capped, relevant subset of an existing repo's source files.

        Returns the files the agents should treat as the codebase to edit. The
        caps keep token usage sane; binaries/lockfiles/vendored dirs are skipped.
        """
        repo = (repo or self.repo).strip()
        if "/" not in repo:
            raise RuntimeError(f"Repository must be 'owner/name' (got '{repo}').")
        paths = [p for p in await self.get_repo_tree(repo, branch=branch) if self._is_source_path(p)]
        paths.sort(key=self._context_priority)

        out: List[RepoFile] = []
        total = 0
        for path in paths[: max_files * 3]:  # scan a bit deeper than we keep
            if len(out) >= max_files or total >= max_bytes:
                break
            rf = await self._read_context_file(repo, path, branch)
            if rf is not None:
                out.append(rf)
                total += len(rf.content or "")
        return out

    # --- high-level template (shared) --------------------------------- #
    async def publish(
        self,
        files: List[RepoFile],
        *,
        title: str,
        repo: Optional[str] = None,
        create_new: bool = False,
        private: bool = True,
        body: str = "",
        branch: Optional[str] = None,
        commit_message: Optional[str] = None,
    ) -> PublishResult:
        """Publish ``files`` to a repo.

        Target resolution (``repo``):
          * ``owner/name`` → that repo (open a branch + PR unless it's missing).
          * ``owner`` only / empty → no repo name, so a NEW repo is created
            (auto-named from ``title``) under the configured/!given owner.

        ``commit_message`` (typically LLM-authored) is used for the commits and
        the PR title; falls back to a ``feat:`` line when not supplied.
        """
        files = [f for f in files if f.path and (f.content or "").strip()]
        if not files:
            raise RuntimeError("No files to publish.")

        target, create_new = self._resolve_repo(repo, title=title, create_new=create_new)

        # Auto-detect when not explicitly forced: existing repo → branch + PR;
        # missing repo → create it and push. This makes the owner-only config
        # ("create a new repo") and the owner/name config ("PR") both just work.
        if not create_new and not await self.repo_exists(target):
            create_new = True

        if create_new:
            return await self._publish_new_repo(
                target, files, title=title, private=private, commit_message=commit_message
            )
        return await self._publish_pull_request(
            target, files, title=title, body=body, branch=branch, commit_message=commit_message
        )

    async def _publish_new_repo(
        self, repo: str, files: List[RepoFile], *, title: str, private: bool,
        commit_message: Optional[str] = None,
    ) -> PublishResult:
        if await self.repo_exists(repo):
            raise RuntimeError(
                f"{repo} already exists — untick 'Create new repository' to open a PR against it."
            )
        ref = await self.create_repo(repo, private=private, description=(title or "")[:200])
        created = f"{ref.owner}/{ref.name}" if ref.owner and ref.name else repo
        repo_url = ref.url or self._url_for(created)
        message = commit_message or f"feat: {title} (initial commit)"
        count = await self.commit_files(created, files, branch=ref.default_branch, message=message)
        return PublishResult(
            mode="new_repo", repo=created, repo_url=repo_url, branch=ref.default_branch,
            files=count, html_url=repo_url, pull_request=None, dry_run=getattr(self, "_dry_run", False),
        )

    async def _publish_pull_request(
        self, repo: str, files: List[RepoFile], *, title: str, body: str, branch: Optional[str],
        commit_message: Optional[str] = None,
    ) -> PublishResult:
        # Existence is guaranteed by ``publish`` (auto-detect / forced create).
        base = await self.get_default_branch(repo)
        branch = branch or self._suggest_branch(title)
        await self.create_branch(repo, branch, from_branch=base)
        message = commit_message or f"feat: {title}"
        count = await self.commit_files(repo, files, branch=branch, message=message)
        pr = await self.open_pull_request(
            repo, head=branch, base=base, title=message,
            body=body or self._pr_body(title, files),
        )
        return PublishResult(
            mode="pull_request", repo=repo, repo_url=self._url_for(repo), branch=branch,
            files=count, html_url=pr.url, pull_request=pr, dry_run=getattr(self, "_dry_run", False),
        )


