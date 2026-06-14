"""Free, offline, in-memory GitHub client — the default provider.

Simulates the two publish modes deterministically (no network, no token, $0) so
the whole "Open PR / create repo" feature is demoable and unit-testable without
a GitHub account. Mirrors ``MockJiraClient``.

* ``exists=False`` → ``publish()`` creates a new repo and pushes (mode ``new_repo``).
* ``exists=True``  → ``publish()`` branches + commits + opens a PR (mode ``pull_request``).
"""
from __future__ import annotations

from typing import List, Optional

from .base import GitHubClient
from .models import GitHubIssue, PullRequest, RepoFile, RepoRef


class MockGitHubClient(GitHubClient):
    name = "mock"
    label = "Mock (free)"

    def __init__(self, repo: str = "demo/sdlc-app", *, owner: str = "", exists: bool = True) -> None:
        # Honor an empty repo when an owner is given (owner-only "create new" mode);
        # only fall back to the demo repo when neither is configured.
        super().__init__(repo if (repo or owner) else "demo/sdlc-app", owner=owner)
        # Repos that "exist" (PR mode). Only a fully-qualified default repo counts;
        # an owner-only/empty config means "no repo yet" → create-new demo.
        self._existing: set[str] = {self.repo} if (exists and self.has_default_repo) else set()
        self._pr_counter = 0
        self._branches: dict[str, list[str]] = {}
        self._committed: dict[str, list[str]] = {}
        self._dry_run = False
        # A couple of demo repos so the UI repo-picker has options offline.
        _seed = self.repo if self.has_default_repo else ""
        self._demo_repos = [r for r in [_seed, "demo/web-app", "demo/api-service"] if r]
        # A small fake codebase so "work on an existing repo" is demoable offline.
        self._tree: dict[str, str] = {
            "app/__init__.py": "",
            "app/main.py": (
                "from flask import Flask\n\n"
                "app = Flask(__name__)\n\n\n"
                "@app.route('/health')\n"
                "def health():\n"
                "    return {'status': 'ok'}\n"
            ),
            "app/auth.py": (
                "# NOTE: insecure placeholder — passwords compared in plaintext!\n"
                "USERS = {}\n\n\n"
                "def login(email, password):\n"
                "    return USERS.get(email) == password\n"
            ),
            "tests/test_health.py": (
                "from app.main import app\n\n\n"
                "def test_health():\n"
                "    client = app.test_client()\n"
                "    assert client.get('/health').status_code == 200\n"
            ),
            "README.md": "# Demo App\n\nA small Flask app used for SDLC-agent demos.\n",
            "requirements.txt": "flask>=3.0\n",
        }
        # Seed a demo issue so inbound import works offline.
        self._issues = {
            1: GitHubIssue(
                number=1,
                title="Add email/password login",
                body="As a user, I want to sign in with email and password so I can access my account.",
                labels=["enhancement", "auth"],
                url=f"{self.repo_url}/issues/1",
            )
        }

    # --- primitives --------------------------------------------------- #
    async def repo_exists(self, repo: str) -> bool:
        return repo in self._existing

    async def create_repo(self, repo: str, *, private: bool = True, description: str = "") -> RepoRef:
        self._existing.add(repo)
        owner, name = self._split(repo)
        return RepoRef(owner=owner, name=name, default_branch="main", url=self._url_for(repo))

    async def get_default_branch(self, repo: str) -> str:
        return "main"

    async def create_branch(self, repo: str, branch: str, *, from_branch: str) -> str:
        self._branches.setdefault(repo, ["main"]).append(branch)
        return branch

    async def commit_files(self, repo: str, files: List[RepoFile], *, branch: str, message: str) -> int:
        self._committed[f"{repo}@{branch}"] = [f.path for f in files]
        return len(files)

    async def open_pull_request(self, repo: str, *, head: str, base: str, title: str, body: str) -> PullRequest:
        self._pr_counter += 1
        n = self._pr_counter
        return PullRequest(number=n, url=f"{self._url_for(repo)}/pull/{n}", branch=head, base=base, title=title)

    async def get_issue(self, number: int, *, repo: Optional[str] = None) -> GitHubIssue:
        base = self._url_for(repo) if repo else self.repo_url
        if number in self._issues and not repo:
            return self._issues[number]
        return GitHubIssue(number=number, title=f"Demo issue #{number}",
                           body="Imported demo issue.", url=f"{base}/issues/{number}")

    async def list_repos(self) -> List[str]:
        # Default + seeded demos + any created during this session, de-duplicated.
        seen: list[str] = []
        for r in [*self._demo_repos, *sorted(self._existing)]:
            if r not in seen:
                seen.append(r)
        return seen

    async def get_repo_tree(self, repo: str, *, branch: Optional[str] = None) -> List[str]:
        # The seeded codebase stands in for any "existing" repo in mock mode.
        return list(self._tree.keys())

    async def get_file(self, repo: str, path: str, *, branch: Optional[str] = None) -> RepoFile:
        return RepoFile(path=path, content=self._tree.get(path, ""))

