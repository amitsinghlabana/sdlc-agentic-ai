"""Tests for the real CloudJiraClient using an httpx MockTransport.

These stay 100% offline/free: no JIRA account, no network — a fake transport
returns canned REST v3 responses so we can assert the client's request shaping
and response parsing (ADF flatten, field mapping, dry-run).
"""
from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import httpx

from app.integrations.jira.cloud import CloudJiraClient
from app.integrations.jira.models import Epic, Story, Subtask


def _settings(**overrides):
    base = dict(
        jira_base_url="https://example.atlassian.net",
        jira_email="me@example.com",
        jira_api_token="secret-token",
        jira_project_key="SDLC",
        jira_story_points_field="customfield_10016",
        jira_default_assignee="",
        jira_subtask_issue_type="Sub-task",
        jira_dry_run=False,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _adf(text: str) -> dict:
    return {"type": "doc", "version": 1, "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": text}]}
    ]}


def _client(handler, **overrides):
    return CloudJiraClient(_settings(**overrides), transport=httpx.MockTransport(handler))


# --------------------------------------------------------------------------- #
# Outbound: create issue
# --------------------------------------------------------------------------- #
def test_create_issue_posts_fields_and_parses_key():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["auth"] = request.headers.get("authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(201, json={"id": "10001", "key": "SDLC-101", "self": "http://x"})

    jira = _client(handler)
    story = Story(summary="Sign in", acceptance_criteria=["valid email"], labels=["auth"], story_points=3)
    created = asyncio.run(jira.create_issue(story, parent_key="SDLC-1"))

    assert created.key == "SDLC-101"
    assert created.url == "https://example.atlassian.net/browse/SDLC-101"
    assert captured["method"] == "POST" and captured["path"].endswith("/rest/api/3/issue")
    assert captured["auth"].startswith("Basic ")  # API-token Basic auth
    fields = captured["body"]["fields"]
    assert fields["project"]["key"] == "SDLC"
    assert fields["parent"]["key"] == "SDLC-1"
    assert "sdlc-agent" in fields["labels"]            # marker label added
    assert fields["customfield_10016"] == 3            # story points mapped
    assert fields["description"]["type"] == "doc"      # ADF, not plain string


def test_create_epic_uses_epic_issue_type():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["fields"]["issuetype"]["name"] == "Epic"
        return httpx.Response(201, json={"key": "SDLC-1"})

    jira = _client(handler)
    created = asyncio.run(jira.create_epic(Epic(summary="Login", description="Auth")))
    assert created.key == "SDLC-1" and created.issue_type == "Epic"


def test_dry_run_does_not_call_transport():
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("dry-run must not perform any HTTP request")

    jira = _client(handler, jira_dry_run=True)
    created = asyncio.run(jira.create_issue(Story(summary="No-op")))
    assert created.key == "SDLC-DRYRUN"


# --------------------------------------------------------------------------- #
# Sub-tasks
# --------------------------------------------------------------------------- #
def test_create_issue_creates_subtasks_under_story():
    posts = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        posts.append(body["fields"])
        # First POST is the story, subsequent are sub-tasks.
        key = f"SDLC-{100 + len(posts)}"
        return httpx.Response(201, json={"key": key})

    jira = _client(handler)
    story = Story(
        summary="Sign in",
        subtasks=[Subtask(summary="Build form UI"), Subtask(summary="Add endpoint")],
    )
    created = asyncio.run(jira.create_issue(story))

    assert created.key == "SDLC-101"
    assert [s.key for s in created.subtasks] == ["SDLC-102", "SDLC-103"]
    # Story POST first, then two sub-task POSTs that reference the story as parent.
    assert posts[0]["issuetype"]["name"] == "Story"
    assert posts[1]["issuetype"]["name"] == "Sub-task"
    assert posts[1]["parent"]["key"] == "SDLC-101"
    assert posts[2]["parent"]["key"] == "SDLC-101"
    assert {s.issue_type for s in created.subtasks} == {"Sub-task"}


# --------------------------------------------------------------------------- #
# Assignee
# --------------------------------------------------------------------------- #
def test_assignee_me_resolves_via_myself():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/myself"):
            return httpx.Response(200, json={"accountId": "acc-123", "displayName": "Me"})
        body = json.loads(request.content)
        assert body["fields"]["assignee"]["accountId"] == "acc-123"
        return httpx.Response(201, json={"key": "SDLC-200"})

    jira = _client(handler, jira_default_assignee="me")
    created = asyncio.run(jira.create_issue(Story(summary="Assigned story")))
    assert created.key == "SDLC-200"
    assert created.assignee == "Me (token owner)"


def test_assignee_email_resolves_via_user_search():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/user/search"):
            assert request.url.params.get("query") == "dev@example.com"
            return httpx.Response(200, json=[{"accountId": "acc-dev", "displayName": "Dev"}])
        body = json.loads(request.content)
        assert body["fields"]["assignee"]["accountId"] == "acc-dev"
        return httpx.Response(201, json={"key": "SDLC-201"})

    jira = _client(handler, jira_default_assignee="dev@example.com")
    created = asyncio.run(jira.create_issue(Story(summary="x")))
    assert created.assignee == "dev@example.com"


def test_per_story_assignee_overrides_default_and_uses_account_id_directly():
    def handler(request: httpx.Request) -> httpx.Response:
        # An accountId (no '@') should be used directly — no lookup endpoint hit.
        assert "/myself" not in request.url.path and "/user/search" not in request.url.path
        body = json.loads(request.content)
        assert body["fields"]["assignee"]["accountId"] == "acc-direct"
        return httpx.Response(201, json={"key": "SDLC-202"})

    jira = _client(handler, jira_default_assignee="me")
    created = asyncio.run(jira.create_issue(Story(summary="x", assignee="acc-direct")))
    assert created.assignee == "acc-direct"


def test_no_assignee_when_unset():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert "assignee" not in body["fields"]
        return httpx.Response(201, json={"key": "SDLC-203"})

    jira = _client(handler)  # default assignee is ""
    created = asyncio.run(jira.create_issue(Story(summary="x")))
    assert created.assignee is None


# --------------------------------------------------------------------------- #
# Inbound: get issue / search
# --------------------------------------------------------------------------- #
def test_get_issue_flattens_adf_description():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/issue/SDLC-5"):
            return httpx.Response(200, json={
                "key": "SDLC-5",
                "fields": {
                    "summary": "Login page",
                    "issuetype": {"name": "Story"},
                    "labels": ["auth"],
                    "description": _adf("As a user, I can sign in."),
                    "subtasks": [
                        {"key": "SDLC-6", "fields": {"summary": "Form UI", "issuetype": {"name": "Sub-task"}}}
                    ],
                },
            })
        return httpx.Response(404, json={"errorMessages": ["not found"]})

    jira = _client(handler)
    issue = asyncio.run(jira.get_issue("sdlc-5"))  # also checks upper-casing
    assert issue.key == "SDLC-5"
    assert "sign in" in issue.description_text
    assert issue.children and issue.children[0].key == "SDLC-6"


def test_search_parses_issues():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/search/jql")
        return httpx.Response(200, json={"issues": [
            {"key": "SDLC-2", "fields": {"summary": "A", "issuetype": {"name": "Story"}}},
            {"key": "SDLC-3", "fields": {"summary": "B", "issuetype": {"name": "Story"}}},
        ]})

    jira = _client(handler)
    results = asyncio.run(jira.search("project = SDLC"))
    assert [r.key for r in results] == ["SDLC-2", "SDLC-3"]


def test_error_response_raises_clean_message():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"errorMessages": ["Field 'summary' is required"]})

    jira = _client(handler)
    try:
        asyncio.run(jira.create_issue(Story(summary="x")))
    except RuntimeError as exc:
        assert "400" in str(exc) and "summary" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected RuntimeError for a 400 response")


# --------------------------------------------------------------------------- #
# Factory selection
# --------------------------------------------------------------------------- #
def test_factory_selects_cloud_when_configured(monkeypatch):
    from app.config import settings
    from app.integrations.jira import get_jira, reset_jira

    monkeypatch.setattr(settings, "jira_provider", "cloud")
    monkeypatch.setattr(settings, "jira_base_url", "https://example.atlassian.net")
    monkeypatch.setattr(settings, "jira_email", "me@example.com")
    monkeypatch.setattr(settings, "jira_api_token", "secret")
    monkeypatch.setattr(settings, "jira_project_key", "SDLC")

    reset_jira()
    try:
        client = get_jira()
        assert client.name == "cloud"
        assert "example.atlassian.net" in client.label
    finally:
        reset_jira()  # restore singleton for other tests



