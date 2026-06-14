"""JIRA integration tests (mock provider — free, deterministic)."""
from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.integrations.jira import get_jira, reset_jira
from app.integrations.jira.mapping import (
    build_adf,
    flatten_adf,
    issue_to_feature_request,
    normalize_issue_key,
    parse_story_bundle,
    story_to_fields,
)
from app.integrations.jira.models import JiraIssue, Story
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _force_mock_jira(monkeypatch):
    """Keep these tests hermetic regardless of the developer's .env.

    If ``JIRA_PROVIDER=cloud`` (with real credentials) is set locally, the factory
    would otherwise return the real CloudJiraClient and these mock-based tests would
    hit live JIRA. Force ``mock`` and reset the cached client around each test.
    """
    monkeypatch.setattr(settings, "jira_provider", "mock")
    monkeypatch.setattr(settings, "jira_project_key", "DEMO")
    monkeypatch.setattr(settings, "jira_base_url", "")
    reset_jira()
    yield
    reset_jira()


# --------------------------------------------------------------------------- #
# Mapping (pure unit tests)
# --------------------------------------------------------------------------- #
def test_parse_story_bundle_handles_object_and_list():
    bundle = parse_story_bundle('{"stories": [{"summary": "A"}]}')
    assert len(bundle.stories) == 1 and bundle.stories[0].summary == "A"

    bare = parse_story_bundle('[{"summary": "B"}]')
    assert bare.stories[0].summary == "B"


def test_build_and_flatten_adf_roundtrip():
    adf = build_adf("As a user, I can log in.", ["Valid email", "401 on bad creds"])
    assert adf["type"] == "doc" and adf["version"] == 1
    text = flatten_adf(adf)
    assert "log in" in text
    assert "Acceptance Criteria" in text
    assert "401 on bad creds" in text


def test_story_to_fields_adds_marker_label_and_parent():
    story = Story(summary="x" * 300, labels=["my label"], issue_type="Story", story_points=5)
    fields = story_to_fields(
        story, project_key="SDLC", parent_key="SDLC-1", story_points_field="customfield_10016"
    )
    assert fields["project"]["key"] == "SDLC"
    assert len(fields["summary"]) == 255  # clamped
    assert fields["parent"]["key"] == "SDLC-1"
    assert "my-label" in fields["labels"]  # spaces stripped
    assert "sdlc-agent" in fields["labels"]  # marker added
    assert fields["customfield_10016"] == 5


def test_issue_to_feature_request_includes_children():
    issue = JiraIssue(
        key="DEMO-1",
        summary="Login",
        description_text="Auth feature",
        acceptance_criteria=["Secure"],
        children=[JiraIssue(key="DEMO-2", summary="Sign in")],
    )
    req = issue_to_feature_request(issue)
    assert "Login" in req and "Auth feature" in req
    assert "Acceptance Criteria:" in req and "- Secure" in req
    assert "Child stories:" in req and "- Sign in" in req


# --------------------------------------------------------------------------- #
# Mock client
# --------------------------------------------------------------------------- #
def test_mock_client_seeds_epic_with_children():
    reset_jira()
    jira = get_jira()
    issue = asyncio.run(jira.get_issue("DEMO-1"))
    assert issue.issue_type == "Epic"
    assert len(issue.children) == 2


def test_mock_create_issue_makes_subtasks():
    reset_jira()
    jira = get_jira()
    story = Story(summary="Sign in", subtasks=[{"summary": "UI"}, {"summary": "API"}])
    created = asyncio.run(jira.create_issue(story))
    assert len(created.subtasks) == 2
    assert all(st.issue_type == "Sub-task" and st.url for st in created.subtasks)
    # Sub-task keys are distinct from the parent story key.
    assert created.key not in {st.key for st in created.subtasks}


def test_mock_default_assignee_is_applied(monkeypatch):
    monkeypatch.setattr(settings, "jira_default_assignee", "me")
    reset_jira()
    jira = get_jira()
    created = asyncio.run(jira.create_issue(Story(summary="x", subtasks=[{"summary": "sub"}])))
    assert created.assignee == "Me (token owner)"
    assert created.subtasks[0].assignee == "Me (token owner)"  # inherited


# --------------------------------------------------------------------------- #
# API endpoints
# --------------------------------------------------------------------------- #
def test_status_endpoint_is_mock_and_hides_token():
    reset_jira()
    data = client.get("/api/jira/status").json()
    assert data["provider"] == "mock"
    assert data["is_mock"] is True
    assert "token" not in data and "api_token" not in data


def test_import_endpoint_builds_request():
    reset_jira()
    data = client.get("/api/jira/import", params={"key": "DEMO-1"}).json()
    assert "Email/password login" in data["request"]
    assert data["issue"]["key"] == "DEMO-1"


# --------------------------------------------------------------------------- #
# Issue-key normalization (tolerant of pasted JIRA URLs)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("MAV-26", "MAV-26"),
        ("  mav-26  ", "MAV-26"),
        ("https://amiitsingh.atlassian.net/browse/MAV-26", "MAV-26"),
        ("https://amiitsingh.atlassian.net/issues?filter=-1&selectedIssue=MAV-26", "MAV-26"),
        # The exact (upper-cased) value the broken UI sent — must still resolve.
        ("HTTPS://AMIITSINGH.ATLASSIAN.NET/ISSUES?FILTER=-1&SELECTEDISSUE=MAV-26", "MAV-26"),
        ("https://x.atlassian.net/jira/software/projects/ABC2/boards/1?selectedIssue=ABC2-15", "ABC2-15"),
    ],
)
def test_normalize_issue_key_extracts(raw, expected):
    assert normalize_issue_key(raw) == expected


@pytest.mark.parametrize("bad", ["", "   ", "not a key", "https://example.com/issues"])
def test_normalize_issue_key_rejects_garbage(bad):
    with pytest.raises(ValueError):
        normalize_issue_key(bad)


def test_import_endpoint_accepts_pasted_url():
    reset_jira()
    url = "https://amiitsingh.atlassian.net/issues?filter=-1&selectedIssue=DEMO-1"
    data = client.get("/api/jira/import", params={"key": url}).json()
    assert data["issue"]["key"] == "DEMO-1"


def test_import_endpoint_rejects_unparseable_key():
    reset_jira()
    resp = client.get("/api/jira/import", params={"key": "https://example.com/no-issue-here"})
    assert resp.status_code == 400


def test_create_stories_endpoint_returns_keys():
    reset_jira()
    payload = {
        "create_epic": True,
        "epic": {"summary": "Login", "description": "Auth"},
        "stories": [
            {
                "summary": "Sign in",
                "acceptance_criteria": ["valid email"],
                "labels": ["auth"],
                "subtasks": [{"summary": "Build UI"}, {"summary": "Add endpoint"}],
            },
            {"summary": "Validate input"},
        ],
    }
    data = client.post("/api/jira/create-stories", json=payload).json()
    assert data["count"] == 2
    assert data["epic"]["key"].startswith("DEMO-")
    assert all(c["key"].startswith("DEMO-") and c["url"] for c in data["created"])
    # First story carries its two sub-tasks back to the caller.
    first = data["created"][0]
    assert len(first["subtasks"]) == 2
    assert all(st["key"].startswith("DEMO-") for st in first["subtasks"])


def test_pipeline_emits_stories_json_artifact():
    resp = client.post("/api/run", json={"request": "Add a login page"}).json()
    names = {a["name"] for a in resp["artifacts"]}
    assert "stories.json" in names
    stories = next(a for a in resp["artifacts"] if a["name"] == "stories.json")
    bundle = parse_story_bundle(stories["content"])
    assert len(bundle.stories) >= 1
    # Stories now include implementation sub-tasks.
    assert any(s.subtasks for s in bundle.stories)

