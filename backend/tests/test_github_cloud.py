"""Tests for the real CloudGitHubClient using an httpx MockTransport.

100% offline/free: a fake transport returns canned GitHub REST responses so we
can assert request shaping (branch ref, base64 file PUT, PR body) and response
parsing — no GitHub account, no network.
"""
from __future__ import annotations

import asyncio
import base64
import json
from types import SimpleNamespace

import httpx

from app.integrations.github.cloud import CloudGitHubClient
from app.integrations.github.models import RepoFile


def _settings(**overrides):
    base = {
        "github_api_url": "https://api.github.com",
        "github_token": "ghp_secret",
        "github_repo": "me/app",
        "github_default_branch": "main",
        "github_private": True,
        "github_dry_run": False,
        "github_ca_bundle": "",
        "github_verify_ssl": True,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _client(handler, **overrides):
    return CloudGitHubClient(_settings(**overrides), transport=httpx.MockTransport(handler))


def _files():
    return [RepoFile(path="app/auth.py", content="x = 1\n"), RepoFile(path="README.md", content="# Feature\n")]


# --------------------------------------------------------------------------- #
# Existing repo → branch + commit + PR
# --------------------------------------------------------------------------- #
def test_publish_existing_repo_opens_pr():
    seen = {"puts": [], "auth": None, "version": None}

    def handler(request: httpx.Request) -> httpx.Response:
        p, m = request.url.path, request.method
        seen["auth"] = request.headers.get("authorization")
        seen["version"] = request.headers.get("x-github-api-version")
        if m == "GET" and p == "/repos/me/app":
            return httpx.Response(200, json={"default_branch": "main"})
        if m == "GET" and p == "/repos/me/app/git/ref/heads/main":
            return httpx.Response(200, json={"object": {"sha": "basesha"}})
        if m == "POST" and p == "/repos/me/app/git/refs":
            assert json.loads(request.content)["ref"] == "refs/heads/sdlc/login"
            return httpx.Response(201, json={})
        if m == "GET" and p.startswith("/repos/me/app/contents/"):
            return httpx.Response(404, json={"message": "Not Found"})  # new file
        if m == "PUT" and p.startswith("/repos/me/app/contents/"):
            seen["puts"].append((p, json.loads(request.content)))
            return httpx.Response(201, json={"content": {"sha": "x"}})
        if m == "POST" and p == "/repos/me/app/pulls":
            body = json.loads(request.content)
            assert body["head"] == "sdlc/login" and body["base"] == "main"
            return httpx.Response(201, json={"number": 42, "html_url": "https://github.com/me/app/pull/42"})
        raise AssertionError(f"unexpected {m} {p}")

    gh = _client(handler)
    result = asyncio.run(gh.publish(_files(), title="login", branch="sdlc/login"))

    assert result.mode == "pull_request"
    assert result.pull_request.number == 42
    assert result.pull_request.url.endswith("/pull/42")
    assert result.files == 2
    assert seen["auth"] == "Bearer ghp_secret"
    assert seen["version"] == "2022-11-28"
    # File content was base64-encoded.
    first_put_body = seen["puts"][0][1]
    assert base64.b64decode(first_put_body["content"]).decode() == "x = 1\n"
    assert first_put_body["branch"] == "sdlc/login"


def test_commit_updates_existing_file_includes_sha():
    def handler(request: httpx.Request) -> httpx.Response:
        p, m = request.url.path, request.method
        if m == "GET" and p == "/repos/me/app":
            return httpx.Response(200, json={"default_branch": "main"})
        if m == "GET" and p == "/repos/me/app/git/ref/heads/main":
            return httpx.Response(200, json={"object": {"sha": "s"}})
        if m == "POST" and p == "/repos/me/app/git/refs":
            return httpx.Response(201, json={})
        if m == "GET" and p == "/repos/me/app/contents/app/auth.py":
            return httpx.Response(200, json={"sha": "existingsha"})  # file already exists
        if m == "PUT" and p == "/repos/me/app/contents/app/auth.py":
            assert json.loads(request.content)["sha"] == "existingsha"
            return httpx.Response(200, json={})
        if m == "POST" and p == "/repos/me/app/pulls":
            return httpx.Response(201, json={"number": 1, "html_url": "u"})
        raise AssertionError(f"unexpected {m} {p}")

    gh = _client(handler)
    asyncio.run(gh.publish([RepoFile(path="app/auth.py", content="y")], title="t", branch="b"))


# --------------------------------------------------------------------------- #
# New repo → create + push to default branch
# --------------------------------------------------------------------------- #
def test_publish_new_repo_creates_then_pushes():
    seen = {"create": None}

    def handler(request: httpx.Request) -> httpx.Response:
        p, m = request.url.path, request.method
        if m == "GET" and p == "/user":
            return httpx.Response(200, json={"login": "me"})  # authed user → POST /user/repos
        if m == "GET" and p == "/repos/me/app":
            return httpx.Response(404, json={"message": "Not Found"})  # doesn't exist
        if m == "POST" and p == "/user/repos":
            seen["create"] = json.loads(request.content)
            return httpx.Response(201, json={"default_branch": "main", "html_url": "https://github.com/me/app"})
        if m == "GET" and p.startswith("/repos/me/app/contents/"):
            return httpx.Response(404, json={"message": "Not Found"})
        if m == "PUT" and p.startswith("/repos/me/app/contents/"):
            return httpx.Response(201, json={})
        raise AssertionError(f"unexpected {m} {p}")

    gh = _client(handler)
    result = asyncio.run(gh.publish(_files(), title="brand new", create_new=True))

    assert result.mode == "new_repo"
    assert result.pull_request is None
    assert result.html_url == "https://github.com/me/app"
    assert seen["create"]["name"] == "app" and seen["create"]["auto_init"] is True
    assert seen["create"]["private"] is True


# --------------------------------------------------------------------------- #
# Dry-run performs no writes
# --------------------------------------------------------------------------- #
def test_dry_run_does_no_writes():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path == "/repos/me/app":
            return httpx.Response(200, json={"default_branch": "main"})
        raise AssertionError("dry-run must not write")

    gh = _client(handler, github_dry_run=True)
    result = asyncio.run(gh.publish(_files(), title="t", branch="b"))
    assert result.mode == "pull_request" and result.dry_run is True


# --------------------------------------------------------------------------- #
# Inbound issue parsing + error handling
# --------------------------------------------------------------------------- #
def test_get_issue_parses_labels():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "number": 5, "title": "Bug", "body": "broken",
            "labels": [{"name": "bug"}, {"name": "p1"}],
            "html_url": "https://github.com/me/app/issues/5",
        })

    gh = _client(handler)
    issue = asyncio.run(gh.get_issue(5))
    assert issue.number == 5 and issue.labels == ["bug", "p1"]


def test_error_body_becomes_runtimeerror():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/repos/me/app" and request.method == "GET":
            return httpx.Response(200, json={"default_branch": "main"})
        if request.url.path == "/repos/me/app/git/ref/heads/main":
            return httpx.Response(200, json={"object": {"sha": "s"}})
        if request.url.path == "/repos/me/app/git/refs":
            return httpx.Response(422, json={"message": "Reference already exists"})
        raise AssertionError("unexpected")

    gh = _client(handler)
    try:
        asyncio.run(gh.publish(_files(), title="t", branch="dup"))
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "Reference already exists" in str(exc)


# --------------------------------------------------------------------------- #
# Reading an existing repo (edit mode): tree + file + capped context
# --------------------------------------------------------------------------- #
def test_get_repo_tree_returns_blob_paths():
    def handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if p == "/repos/me/app":
            return httpx.Response(200, json={"default_branch": "main"})
        if p == "/repos/me/app/git/trees/main":
            return httpx.Response(200, json={"tree": [
                {"path": "app/main.py", "type": "blob"},
                {"path": "app", "type": "tree"},
                {"path": "README.md", "type": "blob"},
            ]})
        raise AssertionError(f"unexpected {p}")

    gh = _client(handler)
    paths = asyncio.run(gh.get_repo_tree("me/app"))
    assert paths == ["app/main.py", "README.md"]  # dirs excluded


def test_get_file_decodes_base64():
    raw = "print('hi')\n"
    b64 = base64.b64encode(raw.encode()).decode()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/repos/me/app/contents/app/main.py":
            return httpx.Response(200, json={"encoding": "base64", "content": b64, "sha": "abc"})
        raise AssertionError("unexpected")

    gh = _client(handler)
    f = asyncio.run(gh.get_file("me/app", "app/main.py", branch="main"))
    assert f.content == raw and f.sha == "abc"


def test_fetch_repo_context_filters_and_reads():
    tree = [
        {"path": "app/main.py", "type": "blob"},
        {"path": "package-lock.json", "type": "blob"},      # skipped (lockfile)
        {"path": "node_modules/x/i.js", "type": "blob"},     # skipped (vendored)
        {"path": "logo.png", "type": "blob"},                # skipped (binary)
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if p == "/repos/me/app":
            return httpx.Response(200, json={"default_branch": "main"})
        if p == "/repos/me/app/git/trees/main":
            return httpx.Response(200, json={"tree": tree})
        if p.startswith("/repos/me/app/contents/"):
            body = base64.b64encode(b"code\n").decode()
            return httpx.Response(200, json={"encoding": "base64", "content": body, "sha": "s"})
        raise AssertionError(f"unexpected {p}")

    gh = _client(handler)
    files = asyncio.run(gh.fetch_repo_context("me/app"))
    paths = [f.path for f in files]
    assert paths == ["app/main.py"]  # only the real source file survives


# --------------------------------------------------------------------------- #
# Actionable error messages for token-scope 403s
# --------------------------------------------------------------------------- #
def test_create_repo_403_explains_token_scope():
    # A token scoped to one repo can't POST /user/repos → 403.
    def handler(request: httpx.Request) -> httpx.Response:
        p, m = request.url.path, request.method
        if m == "GET" and p == "/user":
            return httpx.Response(200, json={"login": "me"})  # authed user → POST /user/repos
        if m == "GET" and p == "/repos/me/new-app":
            return httpx.Response(404, json={"message": "Not Found"})  # doesn't exist
        if m == "POST" and p == "/user/repos":
            return httpx.Response(403, json={"message": "Resource not accessible by personal access token"})
        raise AssertionError(f"unexpected {m} {p}")

    gh = _client(handler)
    try:
        asyncio.run(gh.publish(_files(), title="new", repo="me/new-app", create_new=True))
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        msg = str(exc)
        assert "can't CREATE repositories" in msg
        assert "All repositories" in msg or "'repo' scope" in msg


def test_pr_403_explains_pull_request_permission():
    def handler(request: httpx.Request) -> httpx.Response:
        p, m = request.url.path, request.method
        if m == "GET" and p == "/repos/me/app":
            return httpx.Response(200, json={"default_branch": "main"})
        if m == "GET" and p == "/repos/me/app/git/ref/heads/main":
            return httpx.Response(200, json={"object": {"sha": "s"}})
        if m == "POST" and p == "/repos/me/app/git/refs":
            return httpx.Response(201, json={})
        if m == "GET" and p.startswith("/repos/me/app/contents/"):
            return httpx.Response(404, json={"message": "Not Found"})
        if m == "PUT" and p.startswith("/repos/me/app/contents/"):
            return httpx.Response(201, json={})
        if m == "POST" and p == "/repos/me/app/pulls":
            return httpx.Response(403, json={"message": "Resource not accessible by personal access token"})
        raise AssertionError(f"unexpected {m} {p}")

    gh = _client(handler)
    try:
        asyncio.run(gh.publish(_files(), title="t", repo="me/app", branch="b"))
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "Pull requests: Read and write" in str(exc)


def test_network_block_403_explains_not_a_token_problem():
    # Corporate egress block (e.g. GitHub enterprise allowlist) — reaches GitHub
    # but is rejected at the network layer, NOT a token-scope issue.
    msg = "Your network administrator has blocked access to GitHub except for the 'Mastercard' enterprises."

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"message": msg})

    gh = _client(handler)
    try:
        asyncio.run(gh.repo_exists("me/app"))
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        text = str(exc)
        assert "NETWORK block" in text
        assert "Mock mode" in text


def test_401_hint_points_to_env_local():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Bad credentials"})

    gh = _client(handler)
    try:
        asyncio.run(gh.repo_exists("me/app"))
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert ".env.local" in str(exc)


# --------------------------------------------------------------------------- #
# Repo creation: user vs org routing + owner-mismatch context
# --------------------------------------------------------------------------- #
def test_create_repo_under_org_uses_orgs_endpoint():
    seen = {"path": None}

    def handler(request: httpx.Request) -> httpx.Response:
        p, m = request.url.path, request.method
        if m == "GET" and p == "/user":
            return httpx.Response(200, json={"login": "me"})  # authenticated user
        if m == "GET" and p == "/repos/acme/widget":
            return httpx.Response(404, json={"message": "Not Found"})
        if m == "POST" and p == "/orgs/acme/repos":  # owner != login → org endpoint
            seen["path"] = p
            return httpx.Response(201, json={"full_name": "acme/widget", "default_branch": "main",
                                             "html_url": "https://github.com/acme/widget"})
        if m == "GET" and p.startswith("/repos/acme/widget/contents/"):
            return httpx.Response(404, json={"message": "Not Found"})
        if m == "PUT" and p.startswith("/repos/acme/widget/contents/"):
            return httpx.Response(201, json={})
        raise AssertionError(f"unexpected {m} {p}")

    gh = _client(handler)
    result = asyncio.run(gh.publish(_files(), title="w", repo="acme/widget", create_new=True))
    assert result.mode == "new_repo" and result.repo == "acme/widget"
    assert seen["path"] == "/orgs/acme/repos"


def test_create_repo_owner_mismatch_403_explains():
    def handler(request: httpx.Request) -> httpx.Response:
        p, m = request.url.path, request.method
        if m == "GET" and p == "/user":
            return httpx.Response(200, json={"login": "me"})
        if m == "GET" and p == "/repos/acme/widget":
            return httpx.Response(404, json={"message": "Not Found"})
        if m == "POST" and p == "/orgs/acme/repos":
            return httpx.Response(403, json={"message": "Resource not accessible by personal access token"})
        raise AssertionError(f"unexpected {m} {p}")

    gh = _client(handler)
    try:
        asyncio.run(gh.publish(_files(), title="w", repo="acme/widget", create_new=True))
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        msg = str(exc)
        assert "authenticates as 'me'" in msg and "'acme'" in msg


# --------------------------------------------------------------------------- #
# diagnose() — token capability probe
# --------------------------------------------------------------------------- #
def test_diagnose_classic_token_reports_scopes():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/user"
        return httpx.Response(200, json={"login": "me"},
                              headers={"x-oauth-scopes": "repo, gist"})

    gh = _client(handler)
    info = asyncio.run(gh.diagnose())
    assert info["authenticated_as"] == "me"
    assert info["token_type"] == "classic"
    assert info["can_create_repos"] is True
    assert info["owner_matches"] is True  # owner 'me' from repo me/app


def test_diagnose_fine_grained_cannot_assert_capability():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"login": "me"})  # no x-oauth-scopes header

    gh = _client(handler)
    info = asyncio.run(gh.diagnose())
    assert info["token_type"] == "fine-grained"
    assert info["can_create_repos"] is None


def test_diagnose_flags_owner_mismatch():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"login": "someone-else"},
                              headers={"x-oauth-scopes": "repo"})

    gh = _client(handler, github_owner="acme")
    info = asyncio.run(gh.diagnose())
    assert info["owner_matches"] is False
    assert info["configured_owner"] == "acme"


