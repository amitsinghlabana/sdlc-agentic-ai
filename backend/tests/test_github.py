"""Tests for the GitHub integration — mock client, mapping, factory, endpoints.

All offline/free: the mock client simulates both publish modes; the FastAPI
endpoints run against it. The real client is covered in test_github_cloud.py.
"""
from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from app.config import settings
from app.integrations.github import get_github, reset_github
from app.integrations.github.mapping import artifacts_to_files, issue_to_feature_request
from app.integrations.github.mock import MockGitHubClient
from app.integrations.github.models import GitHubIssue
from app.main import app

client = TestClient(app)


# --------------------------------------------------------------------------- #
# Mapping
# --------------------------------------------------------------------------- #
def test_artifacts_to_files_skips_empty_and_stories_json():
    arts = [
        {"name": "app/auth.py", "content": "print('hi')"},
        {"name": "stories.json", "content": "{}"},   # skipped (machine config)
        {"name": "empty.md", "content": "   "},        # skipped (blank)
        {"name": "README.md", "content": "# Hi"},
    ]
    files = artifacts_to_files(arts)
    paths = [f.path for f in files]
    assert paths == ["app/auth.py", "README.md"]


def test_issue_to_feature_request_includes_title_body_labels():
    issue = GitHubIssue(number=7, title="Add login", body="As a user…", labels=["auth", "ui"])
    req = issue_to_feature_request(issue)
    assert "#7" in req and "Add login" in req and "As a user" in req
    assert "auth, ui" in req


# --------------------------------------------------------------------------- #
# Mock client — two publish modes
# --------------------------------------------------------------------------- #
def _files():
    from app.integrations.github.models import RepoFile
    return [RepoFile(path="app/auth.py", content="x=1"), RepoFile(path="README.md", content="# Feature")]


def test_publish_existing_repo_opens_pull_request():
    gh = MockGitHubClient(repo="me/app", exists=True)
    result = asyncio.run(gh.publish(_files(), title="Add login", branch="sdlc/login"))
    assert result.mode == "pull_request"
    assert result.pull_request is not None
    assert result.pull_request.url.endswith("/pull/1")
    assert result.branch == "sdlc/login"
    assert result.files == 2
    assert result.html_url == result.pull_request.url


def test_publish_new_repo_creates_and_pushes():
    gh = MockGitHubClient(repo="me/brand-new", exists=False)
    result = asyncio.run(gh.publish(_files(), title="New thing", create_new=True))
    assert result.mode == "new_repo"
    assert result.pull_request is None
    assert result.branch == "main"
    assert result.html_url == "https://github.com/me/brand-new"


def test_publish_to_overridden_repo_targets_that_repo():
    # One client, a different target repo per publish (multi-repo).
    gh = MockGitHubClient(repo="me/app", exists=True)
    result = asyncio.run(gh.publish(_files(), title="x", repo="me/other", create_new=True))
    assert result.repo == "me/other"
    assert "me/other" in result.html_url


def test_create_new_on_existing_repo_errors():
    gh = MockGitHubClient(repo="me/app", exists=True)
    try:
        asyncio.run(gh.publish(_files(), title="x", create_new=True))
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "already exists" in str(exc)


def test_pr_on_missing_repo_auto_creates():
    # A fully-qualified repo that doesn't exist yet is auto-created (no error).
    gh = MockGitHubClient(repo="me/ghost", exists=False)
    result = asyncio.run(gh.publish(_files(), title="x"))  # create_new defaults False
    assert result.mode == "new_repo"
    assert result.repo == "me/ghost"


def test_publish_rejects_empty_filelist():
    gh = MockGitHubClient(repo="me/app", exists=True)
    try:
        asyncio.run(gh.publish([], title="x"))
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass


def test_mock_list_repos_includes_default():
    gh = MockGitHubClient(repo="me/app", exists=True)
    repos = asyncio.run(gh.list_repos())
    assert "me/app" in repos
    assert len(repos) >= 1


def test_mock_get_issue_returns_seeded():
    gh = MockGitHubClient(repo="me/app")
    issue = asyncio.run(gh.get_issue(1))
    assert issue.number == 1 and "login" in issue.title.lower()


# --------------------------------------------------------------------------- #
# Owner-only / empty repo → create a NEW repo (auto-named)
# --------------------------------------------------------------------------- #
def test_owner_only_client_has_no_default_repo():
    gh = MockGitHubClient(repo="", owner="amit", exists=True)
    assert gh.owner == "amit"
    assert gh.has_default_repo is False
    # No repo "exists" yet → publishing creates a fresh one.
    result = asyncio.run(gh.publish(_files(), title="Cool Feature"))
    assert result.mode == "new_repo"
    assert result.repo.startswith("amit/sdlc-cool-feature")


def test_empty_repo_in_publish_creates_under_owner():
    gh = MockGitHubClient(repo="", owner="amit", exists=True)
    # Passing just an owner (no name) also creates a new repo.
    result = asyncio.run(gh.publish(_files(), title="Login Page", repo="amit"))
    assert result.mode == "new_repo"
    assert result.repo.startswith("amit/sdlc-login-page")


def test_bare_name_resolves_under_configured_owner():
    # Owner-only config + a bare repo name → that name under the owner (new repo).
    gh = MockGitHubClient(repo="", owner="amit", exists=True)
    result = asyncio.run(gh.publish(_files(), title="x", repo="my-app"))
    assert result.mode == "new_repo"
    assert result.repo == "amit/my-app"


def test_owner_from_repo_when_no_explicit_owner():
    gh = MockGitHubClient(repo="acme/widget", exists=True)
    assert gh.owner == "acme"
    assert gh.repo_name == "widget"
    assert gh.has_default_repo is True


def test_publish_without_owner_errors():
    gh = MockGitHubClient(repo="demo/x", exists=False)
    # Simulate a misconfiguration with neither repo nor owner.
    gh.repo = ""
    gh._owner = ""
    try:
        asyncio.run(gh.publish(_files(), title="x"))
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "owner" in str(exc).lower()


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #
def test_factory_defaults_to_mock():
    reset_github()
    assert get_github().name == "mock"


def test_factory_mock_exists_follows_repo_config(monkeypatch):
    # No repo configured → simulate a fresh repo (exists False → new_repo mode).
    monkeypatch.setattr(settings, "github_repo", "")
    reset_github()
    gh = get_github()
    assert isinstance(gh, MockGitHubClient)
    assert asyncio.run(gh.repo_exists(gh.repo)) is False
    reset_github()


def test_config_github_configured_with_owner_only(monkeypatch):
    # Token + owner (no repo name) is enough for cloud → owner-only create-new mode.
    monkeypatch.setattr(settings, "github_token", "ghp_dummy")
    monkeypatch.setattr(settings, "github_owner", "amit")
    monkeypatch.setattr(settings, "github_repo", "")
    assert settings.github_configured is True


def test_factory_selects_cloud_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "github_provider", "cloud")
    monkeypatch.setattr(settings, "github_token", "ghp_dummy")
    monkeypatch.setattr(settings, "github_repo", "me/app")
    reset_github()
    try:
        assert get_github().name == "cloud"
    finally:
        reset_github()


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
def test_status_endpoint_hides_token():
    reset_github()
    data = client.get("/api/github/status").json()
    assert data["provider"] == "mock" and data["is_mock"] is True
    assert "token" not in data


def test_import_endpoint_builds_request():
    reset_github()
    data = client.get("/api/github/import", params={"number": 1}).json()
    assert data["issue"]["number"] == 1
    assert "login" in data["request"].lower()


def test_publish_endpoint_existing_repo(monkeypatch):
    monkeypatch.setattr(settings, "github_repo", "me/app")  # → mock exists=True
    reset_github()
    payload = {
        "title": "Add login",
        "artifacts": [
            {"name": "app/auth.py", "content": "x=1"},
            {"name": "stories.json", "content": "{}"},  # skipped
        ],
    }
    data = client.post("/api/github/publish", json=payload).json()
    assert data["mode"] == "pull_request"
    assert data["files"] == 1  # stories.json skipped
    assert data["pull_request"]["url"].endswith("/pull/1")


def test_publish_endpoint_rejects_no_files():
    reset_github()
    payload = {"title": "x", "artifacts": [{"name": "stories.json", "content": "{}"}]}
    resp = client.post("/api/github/publish", json=payload)
    assert resp.status_code == 400


def test_repos_endpoint_lists_repos(monkeypatch):
    monkeypatch.setattr(settings, "github_repo", "me/app")
    reset_github()
    data = client.get("/api/github/repos").json()
    assert "me/app" in data["repos"]
    assert data["default"] == "me/app"


def test_publish_endpoint_create_new_repo(monkeypatch):
    monkeypatch.setattr(settings, "github_repo", "me/app")
    reset_github()
    payload = {
        "title": "Fresh project",
        "create_new": True,
        "repo": "me/fresh-project",
        "artifacts": [{"name": "app/main.py", "content": "print('hi')"}],
    }
    data = client.post("/api/github/publish", json=payload).json()
    assert data["mode"] == "new_repo"
    assert data["repo"] == "me/fresh-project"


def test_publish_endpoint_respects_file_selection(monkeypatch):
    monkeypatch.setattr(settings, "github_repo", "me/app")
    reset_github()
    # User selected only one of two real files.
    payload = {
        "title": "Partial",
        "artifacts": [{"name": "app/auth.py", "content": "x=1"}],
    }
    data = client.post("/api/github/publish", json=payload).json()
    assert data["files"] == 1


def test_context_endpoint_previews_repo_files(monkeypatch):
    monkeypatch.setattr(settings, "github_repo", "me/app")
    reset_github()
    data = client.get("/api/github/context", params={"repo": "me/app"}).json()
    assert data["repo"] == "me/app"
    assert data["count"] >= 1
    paths = [f["path"] for f in data["files"]]
    assert any(p.endswith(".py") for p in paths)
    assert all("bytes" in f for f in data["files"])


def test_publish_endpoint_returns_ai_commit_metadata(monkeypatch):
    monkeypatch.setattr(settings, "github_repo", "me/app")
    reset_github()
    payload = {
        "title": "Add logout",
        "request": "Let users log out of the app",
        "artifacts": [{"name": "app/auth.py", "content": "def logout(): ..."}],
    }
    data = client.post("/api/github/publish", json=payload).json()
    # The LLM authors the commit subject (Conventional Commits) + PR text.
    assert data["commit"]["subject"].startswith("feat")
    assert "logout" in data["commit"]["subject"].lower()
    assert data["commit"]["pr_body"]


def test_publish_endpoint_owner_only_creates_new_repo(monkeypatch):
    # Owner configured, no default repo → endpoint creates a fresh repo.
    monkeypatch.setattr(settings, "github_repo", "")
    monkeypatch.setattr(settings, "github_owner", "amit")
    reset_github()
    payload = {
        "title": "Brand New App",
        "artifacts": [{"name": "app/main.py", "content": "print('hi')"}],
    }
    data = client.post("/api/github/publish", json=payload).json()
    assert data["mode"] == "new_repo"
    assert data["repo"].startswith("amit/sdlc-brand-new-app")


def test_status_endpoint_exposes_owner(monkeypatch):
    monkeypatch.setattr(settings, "github_repo", "")
    monkeypatch.setattr(settings, "github_owner", "amit")
    reset_github()
    data = client.get("/api/github/status").json()
    assert data["owner"] == "amit"
    assert data["has_default_repo"] is False


def test_test_endpoint_diagnoses_mock(monkeypatch):
    monkeypatch.setattr(settings, "github_repo", "")
    monkeypatch.setattr(settings, "github_owner", "amit")
    reset_github()
    data = client.get("/api/github/test").json()
    assert data["ok"] is True and data["is_mock"] is True
    assert data["authenticated_as"] == "amit"
    assert data["can_create_repos"] is True
    assert "token" not in data and "hints" in data


